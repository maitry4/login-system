# Import necessary modules
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import pandas as pd
import mysql.connector
import requests
from django.conf import settings
from django.http import JsonResponse
# Create your views here.


# Function to create a Pandas DataFrame from MySQL data
def mysql_dataframe(host, user, password, database, table):
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
        cursor = conn.cursor()

        # Fetch data from the MySQL table
        query = f"SELECT * FROM {table}"
        cursor.execute(query)

        # Fetch all rows and column names
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]

        # Create a Pandas DataFrame
        df = pd.DataFrame(data, columns=column_names)

        return df

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# Create DataFrames from MySQL tables
books = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "books")
ratings = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "ratings")

# Merge ratings and books data
ratings_with_name = ratings.merge(books, on='ISBN')

# Filter users who rated more than 200 books
x = ratings_with_name.groupby('userid').count()['book_rating'] > 200
users_who_rated_more_than_200_books = x[x].index
filtered_rating_based_on_users = ratings_with_name[ratings_with_name['userid'].isin(users_who_rated_more_than_200_books)]

# Filter ratings based on the selected users
y = filtered_rating_based_on_users.groupby('book_title').count()['book_rating'] >= 50
famous_books = y[y].index
# filtered ratings that passes the criteria we set above
final_ratings = filtered_rating_based_on_users[filtered_rating_based_on_users['book_title'].isin(famous_books)]

# Create a pivot table (userid's as column and books as rows)
# every book is a vector in a 810 dimension space
pt = final_ratings.pivot_table(index='book_title', columns='userid', values=['book_rating', 'ISBN'])
# filling in null values (for better data access)
pt.fillna(0, inplace=True)
# every book's distance is being found with every other book so as to find which books are similar
similarity_scores = cosine_similarity(pt)

# Function to suggest similar books
def suggest(book_name:str)->list:
    # index fetch
    book_name = book_name.lower()
    index = np.where(pt.index==book_name)[0][0]

    # Find similar items and their details
    similar_items = sorted(list(enumerate(similarity_scores[index])),key=lambda x:x[1], reverse=True)[1:6]

    # complete information of similar books
    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['book_title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('book_title')['book_title'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['book_author'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['image_url'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['ISBN'].values))

        data.append(item)

    return data

# Create DataFrame for popular books (These are directly fetched from the preprocessed database table)
popular_df = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "top5_books")

# Organize book details
details = {'book': list(popular_df['title'].values),
    'author': list(popular_df['author'].values),
    'image': list(popular_df['image_url'].values),
    'ISBN' : list(popular_df['ISBN'].values)}


restructured_data = []
# Restructure book data (for data representation on the web)
for i in range(5):
    restructured_data.append({
        'book_name': details['book'][i],
        'author': details['author'][i],
        'image_url': details['image'][i],
        'ISBN': details['ISBN'][i],
    })

# View for the index page
def index(request):
    if request.user.is_authenticated:
        try:  
            conn = mysql.connector.connect(host="localhost", user="root", password="maitry", database="book_recommend")
            cursor = conn.cursor()

            # Fetch the user's reading history
            query = "select book_title from reading_history where userid= %s;"
            # Execute the query with the user ID or username as a parameter
            cursor.execute(query, (request.user.id,))

            # Fetch the result
            result = cursor.fetchone()
            try:
                result=result[0]
                # print(result)
                details = suggest(result)
            except Exception:
                details = suggest(result)

            conn.commit()
            cursor.close()
            conn.close()

            return render(request,'index.html', context = {'restructured_data': restructured_data, 'details':details})
        
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        except Exception as e:
            print(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    return render(request,'index.html', context = {'restructured_data': restructured_data})

# View for the book page
@login_required(login_url="login")
def bookpage(request):
    book_name = request.GET.get('book_name')
    author = request.GET.get('author')
    image_url = request.GET.get('image_url')
    ISBN = request.GET.get('ISBN')

    details = suggest(book_name)
    # Retrieve other fields as needed from the session
    return render(request,'BookPage.html', {'book_name': book_name, 'author': author, 'image_url': image_url, 'ISBN': ISBN , 'details':details})

# View for the search page (before search)
# before search
@login_required(login_url="login")
def recommend_ui(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input')
        return redirect('recommend_books/', user_input=user_input)
    
    return render(request, 'recommend.html')
    
# View for the search page (after search)
# after search
@login_required(login_url="login")
def recommend(request):
    user_input = request.POST.get('user_input')
    user_input = str(user_input)
    try:
        data = suggest(user_input)
        return render(request, 'recommend.html', {'data':data})
    except:
        return render(request, 'recommend.html', {'data':'Sorry No such book in our database'})

# View for the signup page
def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        if pass1 != pass2:
            return HttpResponse("Your password and confirm password don't match!")
        else:
            my_user = User.objects.create_user(uname,"", pass1)
            my_user.save()
            return redirect('login')
    return render(request, 'signup.html') 

# View for the login page
def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass')

        user = authenticate(request,username=username, password=pass1)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Incorrect Username or Password!!")
    return render(request, 'login.html') 

# View for the logout page
def LogoutPage(request):
    logout(request)
    return redirect('login')


# View for rating a book
@login_required
def rate_book(request):
    ISBN = request.GET.get('ISBN')
    rating = request.GET.get('selected')
    try:
        rating = int(request.GET.get('selected'))
    except TypeError:
        print("Couldn't rate")
    try:  
        conn = mysql.connector.connect(host="localhost", user="root", password="maitry", database="book_recommend")
        cursor = conn.cursor()
        query = f"insert into ratings(userid, ISBN, book_rating) VALUES (%s, %s, %s)"
        values = (int(request.user.id), ISBN, rating)
        cursor.execute(query, values)
        conn.commit()


        if conn.is_connected():
            cursor.close()
            conn.close()

        return redirect('home')

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return HttpResponse("Couldn't rate")

# View for marking a book as read
@login_required
def mark_as_read(request):
    ISBN = str(request.GET.get('ISBN'))
    book_name = str(request.GET.get('book_name'))
    try:  
        conn = mysql.connector.connect(host="localhost", user="root", password="maitry", database="book_recommend")
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM reading_history WHERE userid = %s"  

        # Execute the query with the user ID or username as a parameter
        cursor.execute(query, (request.user.id,))

        # Fetch the result
        result = cursor.fetchone()

        # Check if the user exists (result will be a tuple with the count)
        if result[0] > 0:
            query1 = "delete from reading_history where userid = %s"
            cursor.execute(query1, (request.user.id,))
        query2 = "insert into reading_history(userid, isbn, book_title) values(%s, %s, %s)"
        values = (request.user.id, ISBN, book_name)
        cursor.execute(query2, (values))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect('home')

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return HttpResponse("Couldn't Mark As Read. Try again later!")

@login_required
def past_read(request):
    pass
