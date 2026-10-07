from django import forms


class SiteForm(forms.Form):
    name = forms.CharField(max_length=100, label="What's your clan called?")
    slug = forms.SlugField(max_length=48, label="Choose your website address")
    game = forms.CharField(max_length=80, required=False, label="What do you play?")


class PageForm(forms.Form):
    title = forms.CharField(max_length=120)
    html = forms.CharField(widget=forms.HiddenInput, required=False, max_length=100000)
    version = forms.IntegerField(widget=forms.HiddenInput, required=False)
