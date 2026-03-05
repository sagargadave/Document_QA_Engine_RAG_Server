from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=200)
    #The uploaded files go into 'media/documents/' folder
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.title
    
    # Method to get the URL for view/edit a single document
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("document_list")
    