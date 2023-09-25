from django.shortcuts import render, redirect
from .forms import BookForm, SearchForm
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
pt = final_ratings.pivot_table(index='book_title', columns='userid', values='book_rating')
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
        print(books['book_title'])
        print(pt.index[i[0]])
        temp_df = books[books['book_title'] == pt.index[i[0]]]
        # print(temp_df)
        item.extend(list(temp_df.drop_duplicates('book_title')['book_title'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['book_author'].values))
        item.extend(list(temp_df.drop_duplicates('book_title')['image_url'].values))

        data.append(item)

    return data

# print(suggest('1984'))

popular_df = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "top5_books")

details = {'book': list(popular_df['title'].values),
    'author': list(popular_df['author'].values),
    'image': list(popular_df['image_url'].values)}


restructured_data = []

for i in range(5):
    restructured_data.append({
        'book_name': details['book'][i],
        'author': details['author'][i],
        'image_url': details['image'][i]
    })
def index(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            # Store form data in the session
            request.session['book_name'] = form.cleaned_data['book_name']
            request.session['author'] = form.cleaned_data['author']
            request.session['image_url'] = form.cleaned_data['image_url']
            # Add more fields as needed

            return redirect('bookpage')
    else:
        form = BookForm()
    return render(request,'index.html', context = {'restructured_data': restructured_data})

def bookpage(request):
    book_name = request.GET.get('book_name')
    author = request.GET.get('author')
    image_url = request.GET.get('image_url')

    details = suggest(book_name)
    # Retrieve other fields as needed from the session
    return render(request,'BookPage.html', {'book_name': book_name, 'author': author, 'image_url': image_url, 'details':details})

# before search
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
def recommend(request):
    user_input = request.POST.get('user_input')
    user_input = str(user_input)
    # print(user_input)
    try:
        data = suggest(user_input)
        return render(request, 'recommend.html', {'data':data})
    except:
        return render(request, 'recommend.html', {'data':'Sorry No such book in our database'})