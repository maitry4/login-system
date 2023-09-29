import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from mysql_to_dataframe import mysql_dataframe


books = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "books")
ratings = mysql_dataframe("localhost", "root", "maitry", "book_recommend", "ratings")


ratings_with_name = ratings.merge(books, on='ISBN')

x = ratings_with_name.groupby('userid').count()['book_rating'] > 200
users_who_rated_more_than_200_books = x[x].index
filtered_rating_based_on_users = ratings_with_name[ratings_with_name['userid'].isin(users_who_rated_more_than_200_books)]

# filtered_rating_based_on_books
y = filtered_rating_based_on_users.groupby('book_title').count()['book_rating'] >= 50
famous_books = y[y].index

final_ratings = filtered_rating_based_on_users[filtered_rating_based_on_users['book_title'].isin(famous_books)]

pt = final_ratings.pivot_table(index='book_title', columns='userid', values='book_rating')
pt.fillna(0, inplace=True)
# every book is a vector in a 810 dimension space
# every book's distance is being found with every other book so as to find which books are similar
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

print(suggest('1984'))