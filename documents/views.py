import os
import re
import ollama
# from openai import OpenAI
from pypdf import PdfReader
from .models import Document
from dotenv import load_dotenv
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


# OLLAMA_MODEL = "mistral"
OLLAMA_MODEL = "gemma3:1b"

load_dotenv() 

# CRUD Views
class DocumentListView(ListView):
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'


class DocumentCreateView(CreateView):
    model = Document
    fields = ['title', 'file'] # Fields to show in the form
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('document_list') # Redirect after successful upload
    
    
class DocumentUpdateView(UpdateView):
    model = Document
    fields = ['title'] # Only allow editing the title
    template_name = 'documents/document_form.html'
    # success_url is handled by get_absolute_url in the model
    
    
class DocumentDeleteView(DeleteView):
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('document_list') # Redirect after successful deletion
    


def simple_rag_pipeline(question, context):
    
    # 1. Retrieval (Simple Keyword Search)
    # 2. Generation (Ollama call)
    
    if not context:
        return "No documents uploaded or able to be read for context."

    # --- 1. Retrieval (Simple Search) ---
    # Find sentences in the context that contain words from the question
    keywords = re.findall(r'\b\w+\b', question.lower())
    relevant_snippets = set()
    
    # Split the context into smaller, manageable chunks (e.g., sentences/paragraphs)
    # This is a very basic retrieval step. Real RAG uses embeddings.
    chunks = re.split(r'(?<=[.!?])\s+', context)
    
    # Simple check: include chunks that contain at least one keyword
    for chunk in chunks:
        if any(keyword in chunk.lower() for keyword in keywords):
            relevant_snippets.add(chunk)
            
    # Combine the top relevant snippets into a final context for the AI
    final_context = " ".join(list(relevant_snippets)[:5]) # Use top 5 snippets
    
    if not final_context:
        return "Couldn't find relevant content in documents using simple keyword search.", None

    # ---  2. Generation (Ollama Call) ---
    try:
        # Ollama does not need an API key as it runs locally
        
        system_prompt = (
            "You are a helpful Q&A assistant. Based ONLY on the following context, "
            "answer the user's question. If the information is not in the context, "
            "state that you cannot answer from the provided documents."
        )

        user_content = f"CONTEXT:\n{final_context}\n\nQUESTION: {question}"

        # Use the ollama.chat function
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        
        # Ollama response structure is a dictionary
        ai_answer = response['message']['content']
        
        return ai_answer, final_context
        
    except Exception as e:
        # Handle errors related to Ollama server connection (e.g., server not running)
        return f"AI Generation Error: Ollama connection failed. Is the Ollama app running and is the '{OLLAMA_MODEL}' model downloaded? Error: {e}", final_context


    """
    --- Generation (AI Call : OpenAI) ---
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"Based ONLY on the following context, answer the user's question. If the information is not in the context, state that you cannot answer from the provided documents.\n\nCONTEXT:\n{final_context}\n\nQUESTION: {question}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Q&A assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content, final_context
    except Exception as e:
        # Handle API errors (e.g., key expired, network issue)
        return f"AI Generation Error: {e}", final_context
    """

def get_document_content(doc):
    # Extract text from a single document.
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)

    text = ""

    try:
        if(doc.file.name.endswith('.pdf')):
            reader = PdfReader(file_path)
            text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif doc.file.name.endswith(('.txt', '.doc', '.docx')):
            with open(file_path, 'r', encodings = 'utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading {doc.title}: {e}")

    return f"--- Document Title: {doc.title} ---\n{text}"


def ask_question(request,doc_id):
    # Ask a question for a specific document.
    answer = None
    question = None
    source_snippet = None

    try:
        doc = Document.objects.get(pk=doc_id)
    except Document.DoesNotExist:
        return render(request, 'documents/ask_question.html', {'error': "Document not found."})


    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if question:
            # 1. Fetch all document content
            context = get_document_content(doc) 

            # 2. Run the simple RAG pipeline
            result, source_snippet = simple_rag_pipeline(question, context)
            answer = result

    return render(request, 'documents/ask_question.html', {
        'answer': answer,
        'question': question,
        'source_snippet': source_snippet,
        'document' : doc,
    })
