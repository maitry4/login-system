# forms.py

from django import forms

class BookForm(forms.Form):
    book_name = forms.CharField()
    author = forms.CharField()
    image_url = forms.URLField()
    ISBN = forms.CharField()
    # Add more form fields as needed

class RatingForm(forms.Form):
    rating = forms.IntegerField(
    widget=forms.HiddenInput(),
    )
