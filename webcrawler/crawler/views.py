import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import boto3
import re
from .scraper import scrape_url
from dotenv import load_dotenv
import os
import variables as vars

load_dotenv()


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('ask')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'ask')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return redirect('/admin')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# @login_required(login_url='login')
@csrf_exempt
def ask(request):
    """Main chat interface - requires authentication"""
    response = ""
    if request.method == "POST":
        prompt = request.POST.get("question", "")
        
        if not prompt.strip():
            messages.error(request, 'Please enter a question.')
            return render(request, "form.html")

        try:
            # Match command like: "Crawl this URL: https://example.com"
            match = re.search(r'Crawl this URL:\s*(https?://\S+)', prompt)
            if match:
                url = match.group(1)
                scraped = scrape_url(url)
                full_prompt = f"Here is the text from the page:\n{scraped}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Call Bedrock Claude model
            session = boto3.Session(
                aws_access_key_id=vars.AWS_ACCESS_KEY,
                aws_secret_access_key=vars.AWS_SECRET_ACCESS_KEY,
                region_name='us-east-1'
            )

            bedrock = session.client('bedrock-runtime')

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": full_prompt}],
                "max_tokens": 512,
            }

            response = bedrock.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(body),
                contentType="application/json"
            )
            
            output = response['body'].read().decode()
            response_data = json.loads(output)
            print(response_data)
            breakpoint()
            
            # Extract the actual response text from Claude's response
            if 'content' in response_data and len(response_data['content']) > 0:
                actual_response = response_data['content'][0]['text']
            else:
                actual_response = "No response received from the AI model."
            
            return render(request, "result.html", {
                "response": actual_response,
                "user": request.user,
                "prompt": prompt
            })
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, "form.html")

    return render(request, "form.html", {"user": request.user})


def generate_claude_prompt(user_input):
    """Generate properly formatted Claude prompt"""
    # Remove the JSON wrapping since we're already sending JSON in the body
    return user_input.replace('"', '\\"')


# Optional: API endpoint for AJAX requests
@login_required(login_url='login')
@csrf_exempt
def ask_api(request):
    """API endpoint for chat requests - requires authentication"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        prompt = data.get("question", "")
        
        if not prompt.strip():
            return JsonResponse({"error": "Question cannot be empty"}, status=400)

        # Match command like: "Crawl this URL: https://example.com"
        match = re.search(r'Crawl this URL:\s*(https?://\S+)', prompt)
        if match:
            url = match.group(1)
            scraped = scrape_url(url)
            full_prompt = f"Here is the text from the page:\n{scraped}\n\n{prompt}"
        else:
            full_prompt = prompt

        # Call Bedrock Claude model
        session = boto3.Session(
            aws_access_key_id=vars.AWS_ACCESS_KEY,
            aws_secret_access_key=vars.AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1'
        )

        bedrock = session.client('bedrock-runtime')

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": full_prompt}],
            "max_tokens": 512,
        }

        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0", 
            body=json.dumps(body),
            contentType="application/json"
        )
        
        output = response['body'].read().decode()
        response_data = json.loads(output)
        
        # Extract the actual response text from Claude's response
        if 'content' in response_data and len(response_data['content']) > 0:
            actual_response = response_data['content'][0]['text']
        else:
            actual_response = "No response received from the AI model."
        
        return JsonResponse({
            "response": actual_response,
            "success": True
        })
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "success": False
        }, status=500)
