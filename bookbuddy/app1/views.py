from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# from .forms import BookForm, RatingForm
# from .models import ReadingHistory
# from .mysql_to_dataframe import mysql_dataframe
# from .collaborative_filt_model import suggest
import pandas as pd
import mysql.connector

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
# Create your views here.

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
# from mysql_to_dataframe import mysql_dataframe



books = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "books")
ratings = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "ratings")


ratings_with_name = ratings.merge(books, on='ISBN')

x = ratings_with_name.groupby('userid').count()['book_rating'] > 200
users_who_rated_more_than_200_books = x[x].index
# filtered_rating_based_on_users (padhe_likhe_users)
filtered_rating_based_on_users = ratings_with_name[ratings_with_name['userid'].isin(users_who_rated_more_than_200_books)]

# filtered_rating_based_on_books
y = filtered_rating_based_on_users.groupby('book_title').count()['book_rating'] >= 50
famous_books = y[y].index

final_ratings = filtered_rating_based_on_users[filtered_rating_based_on_users['book_title'].isin(famous_books)]
# print(final_ratings)
# filtered ratings that passes the criteria we set above
pt = final_ratings.pivot_table(index='book_title', columns='userid', values=['book_rating', 'ISBN'])
pt.fillna(0, inplace=True)

similarity_scores = cosine_similarity(pt)
def suggest(book_name:str)->list:
    # index fetch
    book_name = book_name.lower()
    index = np.where(pt.index==book_name)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])),key=lambda x:x[1], reverse=True)[1:6]

    data = []
    for i in similar_items:
        item = []
        # print(books['book_title'])
        # print(pt.index[i[0]])
        temp_df = books[books['book_title'] == pt.index[i[0]]]
        # print(temp_df)
        item.extend(list(temp_df.drop_duplicates('book_title')['book_title'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['book_author'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['image_url'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['ISBN'].values))

        data.append(item)

    return data

# print(suggest('1984'))

popular_df = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "top5_books")

details = {'book': list(popular_df['title'].values),
    'author': list(popular_df['author'].values),
    'image': list(popular_df['image_url'].values),
    'ISBN' : list(popular_df['ISBN'].values)}


restructured_data = []

for i in range(5):
    restructured_data.append({
        'book_name': details['book'][i],
        'author': details['author'][i],
        'image_url': details['image'][i],
        'ISBN': details['ISBN'][i],
    })
def index(request):
    if request.user.is_authenticated:
        try:  
            conn = mysql.connector.connect(host="localhost", user="root", password="maitry", database="book_recommend")
            cursor = conn.cursor()
            print(f"{request}")
            query = "select book_title from reading_history where userid= %s;"
            # Execute the query with the user ID or username as a parameter
            cursor.execute(query, (request.user.id,))

            # Fetch the result
            result = cursor.fetchone()
            try:
                result=result[0]
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

@login_required(login_url="login")
def bookpage(request):
    book_name = request.GET.get('book_name')
    author = request.GET.get('author')
    image_url = request.GET.get('image_url')
    ISBN = request.GET.get('ISBN')

    details = suggest(book_name)
    # Retrieve other fields as needed from the session
    return render(request,'BookPage.html', {'book_name': book_name, 'author': author, 'image_url': image_url, 'ISBN': ISBN , 'details':details})

# before search
@login_required(login_url="login")
def recommend_ui(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input')
        # form = SearchForm(request.POST)
        # if form.is_valid():
        #     # Store form data in the session
        #     request.session['user_input'] = form.cleaned_data['user_name']
            
        #     # Add more fields as needed

        return redirect('recommend_books/', user_input=user_input)
    
    return render(request, 'recommend.html')
    
# after search
@login_required(login_url="login")
def recommend(request):
    user_input = request.POST.get('user_input')
    user_input = str(user_input)
    # print(user_input)
    try:
        data = suggest(user_input)
        print(data)
        return render(request, 'recommend.html', {'data':data})
    except:
        return render(request, 'recommend.html', {'data':'Sorry No such book in our database'})
    

@login_required(login_url='login')
def HomePage(request):
    return render(request, 'home.html')


def SignupPage(request):
    if request.method == 'POST':
        # print("hello")
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


def LogoutPage(request):
    logout(request)
    return redirect('login')



@login_required
def rate_book(request):
    ISBN = request.GET.get('ISBN')
    rating = request.GET.get('selected')
    try:
        rating = int(request.GET.get('selected'))
    except TypeError:
        print("Couldn't rate")
    print(ISBN, rating)
    try:  
        conn = mysql.connector.connect(host="localhost", user="root", password="maitry", database="book_recommend")
        cursor = conn.cursor()
        # print("I am here")
        # print(request.user.id)
        # print(f"insert into ratings(userid, ISBN, book_rating) values({request.user.id}, {ISBN}, {rating})")
        query = f"insert into ratings(userid, ISBN, book_rating) VALUES (%s, %s, %s)"
        values = (int(request.user.id), ISBN, rating)
        cursor.execute(query, values)
        conn.commit()
        # print("Rated successfully!")


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

@login_required
def mark_as_read(request):
    ISBN = str(request.GET.get('ISBN'))
    book_name = str(request.GET.get('book_name'))
    try:  
        conn = mysql.connector.connect(host="localhost", user="root", password="maitry", database="book_recommend")
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM reading_history WHERE userid = %s"  # Change 'user_id' to your actual column name

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
