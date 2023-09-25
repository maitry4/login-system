# forms.py

from django import forms

class BookForm(forms.Form):
    book_name = forms.CharField()
    author = forms.CharField()
    image_url = forms.URLField()
    # Add more form fields as needed


