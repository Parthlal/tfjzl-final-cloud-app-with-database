from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Course, Enrollment, Submission, Question, Choice

def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)

    if request.method == "POST":
        # Create a new submission instance for the enrollment
        submission = Submission.objects.create(enrollment=enrollment)
        
        # Collect selected choices from POST request
        # Form checkboxes use name="choice_{{ question.id }}" or submit choice IDs directly
        selected_choice_ids = []
        for key, value in request.POST.items():
            if key.startswith('choice_'):
                # Handles multiple selections per question if sent as a list
                choices = request.POST.getlist(key)
                selected_choice_ids.extend(choices)
            elif key == 'choice':
                selected_choice_ids.extend(request.POST.getlist('choice'))

        # Retrieve matching Choice objects and add them to the submission
        choices = Choice.objects.filter(id__in=selected_choice_ids)
        submission.choices.set(choices)
        submission.save()

        return redirect("onlinecourse:show_exam_result", course_id=course.id, submission_id=submission.id)

    return redirect("onlinecourse:course_details", course_id=course.id)


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    # Extract selected choice IDs from the submission
    selected_ids = submission.choices.values_list('id', flat=True)
    
    total_score = 0
    possible_score = 0
    
    # Collect all questions across lessons for this course
    questions = Question.objects.filter(lesson__course=course)
    
    for question in questions:
        possible_score += question.grade
        # Evaluate if the user earned score for this question
        if question.is_get_score(selected_ids):
            total_score += question.grade

    # Calculate percentage score
    grade_percentage = int((total_score / possible_score) * 100) if possible_score > 0 else 0

    context = {
        "course": course,
        "submission": submission,
        "questions": questions,
        "total_score": total_score,
        "possible_score": possible_score,
        "grade_percentage": grade_percentage,
    }
    
    return render(request, "onlinecourse/exam_result_bootstrap.html", context)
