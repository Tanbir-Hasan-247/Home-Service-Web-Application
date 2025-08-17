from datetime import datetime
import random
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.db import transaction
from .models import (
    Response,
    State,
    workers,
    users,
    ServiceCatogarys,
    Country,
    City,
    Feedback,
    ServiceRequests,
)
from .forms import stateform


class Commenlib:
    def __init__(self):
        self.DEFAULT_REDIRECT_PATH = {"ROOT": "/"}


common_lib = Commenlib()


# Create your views here.
class Login(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        username = request.POST["uname"]
        password = request.POST["psw"]
        user = authenticate(username=username, password=password)
        print(user)
        # print(user.username)

        if user is not None:
            login(request, user)
            if user.is_superuser and user.is_staff:
                return HttpResponseRedirect("/admmin_home")
                # return render(request, 'adminhome.html')

            elif user.is_staff:
                return HttpResponseRedirect("/workers_home")
            else:
                return redirect("index")
        else:
            return render(request, "login.html", {"error_msg": "Invalid credentials."})


def logout_view(request):
    logout(request)
    # return redirect('login')
    return redirect("login")


class User_Register(View):
    def get(self, request):
        return render(request, "user_register.html")

    def post(self, request):
        first_name = request.POST.get("firstname")
        last_name = request.POST.get("lastname")
        email = request.POST.get("email")
        contact_number = request.POST.get("contactnumber")
        address = request.POST.get("address")
        profile_pics = request.FILES.get("profile_pic")
        gender = request.POST.get("gender")
        # user_type = request.POST.get('usertype')
        password = request.POST.get("password")
        cpassword = request.POST.get("cpassword")
        # user_type= 3
        # Check if passwords match
        if password == cpassword:
            new_user = User.objects.create(
                username=email,
                email=email,
                password=make_password(password),
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_staff=False,
            )

            users.objects.create(
                admin=new_user,
                Address=address,
                gender=gender,
                contact_number=contact_number,
                profile_pic=profile_pics,
            )
            return render(request, "login.html", {"msg": "Addd succsfully!"})

        else:
            return render(
                request, "user_register.html", {"msg": "Passwords do not match!"}
            )

        return render(request, "user_register.html", {"msg": "Something went wrong"})


# HomeServices_app/views.py

# ... your other imports
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.contrib import messages

# ...

# In your views.py file

# In your views.py file


class EditProfileView(LoginRequiredMixin, View):
    """
    Handles both displaying and processing the user profile edit form.
    """

    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]
    template_name = "userpages/edit_profile.html"

    def get(self, request):
        user_profile = get_object_or_404(users, admin=request.user)
        context = {"data": user_profile}
        return render(request, self.template_name, context)

    def post(self, request):
        user_profile = get_object_or_404(users, admin=request.user)

        # Update User model fields
        request.user.first_name = request.POST.get("first_name")
        request.user.last_name = request.POST.get("last_name")
        request.user.save()

        # Update the related 'users' profile model
        user_profile.contact_number = request.POST.get("contact_number")
        user_profile.Address = request.POST.get("address")  # Corrected to lowercase
        user_profile.gender = request.POST.get("gender")

        if "profile_pic" in request.FILES:
            user_profile.profile_pic = request.FILES["profile_pic"]

        user_profile.save()

        messages.success(request, "Your profile has been updated successfully!")

        # --- THIS IS THE FIX ---
        # Redirect to the main profile page instead of the edit page.
        return redirect("userprofile")


class DeleteProfileView(LoginRequiredMixin, View):
    """
    Handles user profile deletion with a POST request.
    """

    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def post(self, request):
        user_to_delete = request.user
        logout(request)  # Log the user out before deleting
        user_to_delete.delete()  # This will cascade and delete the 'users' profile too

        # Cannot use messages framework here as the session is destroyed on logout.
        # A redirect to a success page or homepage is best.
        return redirect("index")  # Redirect to the homepage after deletion


# In your views.py file


class Worker_Register(View):
    def get(self, request):
        designations = ServiceCatogarys.objects.all()
        context = {"designations": designations}
        return render(request, "workers_registration.html", context)

    def post(self, request):
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        # ... get other form fields ...
        password = request.POST.get("password")
        cpassword = request.POST.get("cpassword")

        # --- THIS IS THE FIX ---
        # 1. Check if a user with this email already exists
        if User.objects.filter(username=email).exists():
            # If the user exists, show an error message and re-render the form
            messages.error(
                request, "An account with this email address already exists."
            )
            designations = ServiceCatogarys.objects.all()
            return render(
                request, "workers_registration.html", {"designations": designations}
            )

        # 2. Check if passwords match
        if password != cpassword:
            messages.error(request, "Passwords do not match!")
            designations = ServiceCatogarys.objects.all()
            return render(
                request, "workers_registration.html", {"designations": designations}
            )

        # --- END OF FIX ---

        # If checks pass, create the user
        new_user = User.objects.create_user(  # Using create_user is safer
            username=email,
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname,
            is_active=True,
            is_staff=True,
        )

        # Create the worker profile
        workers.objects.create(
            admin=new_user,
            contact_number=request.POST.get("contactnumber"),
            dob=request.POST.get("dob"),
            Address=request.POST.get("address"),
            city=request.POST.get("city"),
            gender=request.POST.get("gender"),
            designation=request.POST.get("designation"),
            profile_pic=request.FILES.get("profile_pic"),
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")


# HomeServices_app/views.py

# ... your other imports


class EditWorkerProfileView(LoginRequiredMixin, View):
    """
    Handles displaying and processing the worker profile edit form.
    """

    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]
    template_name = "workerpages/edit_worker_profile.html"

    def get(self, request):
        # The 'data' context variable is used to pre-populate the form
        worker_profile = get_object_or_404(workers, admin=request.user)
        context = {"data": worker_profile}
        return render(request, self.template_name, context)

    def post(self, request):
        worker_profile = get_object_or_404(workers, admin=request.user)

        # Update standard User model fields
        request.user.first_name = request.POST.get("first_name")
        request.user.last_name = request.POST.get("last_name")
        request.user.save()

        # Update the related 'workers' profile model
        worker_profile.contact_number = request.POST.get("contact_number")
        worker_profile.dob = request.POST.get("dob")
        worker_profile.Address = request.POST.get("Address")
        worker_profile.city = request.POST.get("city")
        worker_profile.gender = request.POST.get("gender")

        if "profile_pic" in request.FILES:
            worker_profile.profile_pic = request.FILES["profile_pic"]

        worker_profile.save()

        messages.success(request, "Your profile has been updated successfully!")
        return redirect("workerprofile")


class DeleteWorkerProfileView(LoginRequiredMixin, View):
    """
    Handles worker profile deletion.
    """

    def post(self, request):
        user_to_delete = request.user
        logout(request)
        user_to_delete.delete()
        return redirect("index")


class ToggleAvailabilityView(LoginRequiredMixin, View):
    """
    Toggles the worker's availability status.
    """

    def post(self, request):
        worker = get_object_or_404(workers, admin=request.user)
        worker.avalability_status = not worker.avalability_status
        worker.save()
        return redirect("workerprofile")


from django.shortcuts import render

# ... (your other views are here) ...


def signup_selection_view(request):
    """
    A view to render the page where the user chooses to sign up
    as a customer or a service provider.
    """
    return render(request, "signup_selection.html")


class home(View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        services = ServiceCatogarys.objects.all()
        feedbacks = Feedback.objects.select_related("User").all()
        all_services = list(
            ServiceCatogarys.objects.all()
        )  # Convert QuerySet to a list
        sample_size = min(3, len(all_services))
        selected_services = random.sample(
            all_services, sample_size
        )  # Select 6 random services
        print("services:", services)
        context = {
            "services": services,
            "feedbacks": feedbacks,
            "selected_services": selected_services,
        }
        return render(request, "userpages/index.html", context)


class about(View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        return render(request, "userpages/about.html")


class services(View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        services = ServiceCatogarys.objects.all()
        feedbacks = Feedback.objects.select_related("User").all()
        all_services = list(
            ServiceCatogarys.objects.all()
        )  # Convert QuerySet to a list
        # Select 6 random services
        print("services:", services)
        context = {
            "services": services,
            "feedbacks": feedbacks,
        }
        return render(request, "userpages/service.html", context)


# At the top of your views.py file, make sure these are imported
from django.shortcuts import render, redirect
from django.contrib import messages

# ... your other imports and views


class bookservice(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        # Your get method remains the same
        services = ServiceCatogarys.objects.get(id=id)
        city = City.objects.all()
        context = {
            "services": services,
            "city": city,
        }
        return render(request, "userpages/servicebook.html", context)

    def post(self, request, id):
        # Your form processing logic remains the same
        user_id = request.user.id
        user = users.objects.get(admin=user_id)
        problem_description = request.POST.get("Problem_Description")
        service_id = ServiceCatogarys.objects.get(id=id)
        address = request.POST.get("Address")
        city_id = request.POST.get("city")
        pin = request.POST.get("Pincode")
        house_no = request.POST.get("House_No")
        landmark = request.POST.get("landmark")
        contact = request.POST.get("contact")

        service_request = ServiceRequests(
            user=user,
            Problem_Description=problem_description,
            service=service_id,
            Address=address,
            city_id=city_id,
            pin=pin,
            House_No=house_no,
            landmark=landmark,
            contact=contact,
        )
        service_request.save()

        # UPDATED PART: Add a success message and redirect
        messages.success(
            request,
            f"Your request for '{service_id.Name}' has been successfully submitted! We will contact you shortly.",
        )
        return redirect("services")


# HomeServices_app/views.py

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.functions import TruncMonth
from django.utils import timezone
import json # Import the json library at the top

# ...

# In your views.py

class admmin_home(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request):
        # --- Your existing stats are fine ---
        total_requests = ServiceRequests.objects.count()
        completed_requests = Response.objects.filter(status=True).count()
        assigned_requests_count = Response.objects.count()
        pending_requests = assigned_requests_count - completed_requests
        total_users = User.objects.filter(is_staff=False, is_superuser=False).count() # More accurate user count
        latest_requests = ServiceRequests.objects.order_by('-dateofrequest')[:5]

        # --- Data for User Growth Chart ---
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        user_signups = User.objects.filter(date_joined__gte=six_months_ago)\
            .annotate(month=TruncMonth('date_joined'))\
            .values('month')\
            .annotate(count=Count('id'))\
            .order_by('month')
            
        chart_labels = [signup['month'].strftime('%B') for signup in user_signups]
        chart_data = [signup['count'] for signup in user_signups]

        # --- NEW: Calculate data for the service bookings chart ---
        booking_counts = ServiceRequests.objects.filter(dateofrequest__gte=six_months_ago)\
            .annotate(month=TruncMonth('dateofrequest'))\
            .values('month')\
            .annotate(count=Count('id'))\
            .order_by('month')
        
        bookings_chart_labels = [booking['month'].strftime('%B') for booking in booking_counts]
        bookings_chart_data = [booking['count'] for booking in booking_counts]
        # --- END OF NEW CODE ---

        context = {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
            'total_users': total_users,
            'latest_requests': latest_requests,
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
            # Pass the new booking data to the template
            'bookings_chart_labels': json.dumps(bookings_chart_labels),
            'bookings_chart_data': json.dumps(bookings_chart_data),
        }
        return render(request, "adminpages/adminhompage.html", context)

    def test_func(self):
        return self.request.user.is_superuser


# At the top of your views.py, make sure these are imported
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg, Count

# ... your other imports and views


# REPLACE your old workers_home view with this one
class workers_home(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        try:
            # Get the worker instance linked to the logged-in user
            worker_instance = get_object_or_404(workers, admin=request.user)

            # Get all jobs (responses) assigned to this worker
            my_responses = Response.objects.filter(assigned_worker=worker_instance)

            # Calculate personalized stats
            my_completed_jobs = my_responses.filter(status=True).count()
            my_active_jobs = my_responses.filter(status=False).count()

            # Get feedback stats for this worker
            my_feedbacks = Feedback.objects.filter(Employ=worker_instance)
            my_total_reviews = my_feedbacks.count()
            my_avg_rating_result = my_feedbacks.aggregate(avg=Avg("Rating"))
            my_avg_rating = my_avg_rating_result["avg"] or 0

            # Get the 3 most recent active jobs to show as a to-do list
            recent_active_jobs = my_responses.filter(status=False).order_by("-Date")[:3]

            context = {
                "completed_jobs": my_completed_jobs,
                "active_jobs": my_active_jobs,
                "total_reviews": my_total_reviews,
                "average_rating": my_avg_rating,
                "recent_jobs": recent_active_jobs,
            }
        except workers.DoesNotExist:
            # Handle case where user is staff but not in worker table
            context = {}

        return render(request, "workerpages/Workerhompage.html", context)


class contact(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        return render(request, "userpages/contact.html")


class manageworker(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        workers_records = workers.objects.all()
        context = {"workers_records": workers_records}
        return render(request, "adminpages/Manage_Workers.html", context)


# In your views.py file
from django.contrib import messages  # Make sure messages is imported


class verify_worker(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, action, id):
        worker_to_verify = get_object_or_404(workers, id=id)

        if action == "active" and not worker_to_verify.acc_activation:
            worker_to_verify.acc_activation = True
            worker_to_verify.save()
            # Add a success message
            messages.success(
                request,
                f"Worker '{worker_to_verify.admin.get_full_name()}' has been successfully verified.",
            )

        return redirect("manageworker")


class manageusers(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        users_records = users.objects.all()
        context = {"users_records": users_records}
        return render(request, "adminpages/View_Users.html", context)


# HomeServices_app/views.py


class ManageCountry(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]
    template_name = "adminpages/Manage_Country.html"

    def get(self, request):
        country_records = Country.objects.all().order_by("name")
        context = {
            "Country_record": country_records,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        country_name = request.POST.get("name")
        if country_name:  # Basic validation
            Country.objects.create(name=country_name)
            # You can add a success message here if you want
        return redirect("ManageCountry")


class DeleteCountry(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        data = Country.objects.get(id=id)
        data.delete()
        return HttpResponseRedirect("/ManageCountry")


# ... your other imports
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages

# ... your other imports


class DeleteUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Handles the deletion of a user account by a superuser.
    """

    def post(self, request, user_id):
        # Check if the admin is trying to delete their own account
        if request.user.id == user_id:
            messages.error(request, "You cannot delete your own admin account.")
            return redirect("manageusers")

        # If not deleting self, proceed with the deletion
        user_to_delete = get_object_or_404(User, pk=user_id)
        messages.success(
            request, f"Successfully deleted user: {user_to_delete.username}"
        )
        user_to_delete.delete()
        return redirect("manageusers")

    def test_func(self):
        # This part is correct and ensures only superusers can access this view
        return self.request.user.is_superuser


class DeleteWorkerView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Handles the final deletion of a worker account.
    """

    def post(self, request, worker_id):
        worker_to_delete = get_object_or_404(workers, pk=worker_id)

        # It's safer to delete the User object, which will cascade to the worker profile
        user_account = worker_to_delete.admin

        messages.success(
            request, f"Successfully deleted worker: {user_account.username}"
        )
        user_account.delete()

        return redirect("manageworker")

    def test_func(self):
        return self.request.user.is_superuser


# HomeServices_app/views.py
from .forms import stateform  # Make sure this is imported at the top

# ... your other imports and views


# REPLACE your old ManageState and AddState views with this one class
class ManageState(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]
    template_name = "adminpages/ManageState.html"

    def get(self, request):
        state_records = State.objects.select_related("country").all()
        form = stateform()
        context = {"State_record": state_records, "form": form}
        return render(request, self.template_name, context)

    def post(self, request):
        form = stateform(request.POST)
        if form.is_valid():
            form.save()
            # You can add a success message here if you want
            return redirect("ManageState")
        else:
            # If form is invalid, re-render the page with the form and its errors
            state_records = State.objects.select_related("country").all()
            context = {
                "State_record": state_records,
                "form": form,  # Pass the invalid form back to show errors
            }
            return render(request, self.template_name, context)


class DeleteState(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        data = State.objects.get(id=id)
        data.delete()
        return HttpResponseRedirect("/ManageState")


# HomeServices_app/views.py


class managecity(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        city_records = City.objects.all()

        # --- NEW: Fetch states to populate the 'Add City' form ---
        states = State.objects.all()

        context = {
            "city_records": city_records,
            "state_recorsd": states,  # Pass states to the template
        }
        return render(request, "adminpages/ManageCity.html", context)


class AddCity(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        states = State.objects.all()
        return render(request, "city.html", {"state_recorsd": states})

    def post(self, request):
        city_name = request.POST.get("name")
        state = request.POST.get("state")
        City.objects.create(name=city_name, state=state)
        return HttpResponseRedirect("/managecity")


class DeleteCity(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        data = City.objects.get(id=id)
        data.delete()
        return HttpResponseRedirect("/managecity")


class AddServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        return render(request, "adminpages/ServiceCatogry.html")

    def post(self, request):
        Name = request.POST.get("Name")
        Description = request.POST.get("Description")
        img = request.FILES.get("img")
        ServiceCatogarys.objects.create(Name=Name, Description=Description, img=img)

        return HttpResponseRedirect("/ManageServices")


class ManageServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        service_records = ServiceCatogarys.objects.all()
        context = {
            "services": service_records,
        }
        return render(request, "adminpages/Manage_Services.html", context)

        # form = ServiceCatogoryForm(request.POST,request.FILES)
        # if form.is_valid():
        #     form.save()
        #     return HttpResponse("Ok")
        # else:
        #     return HttpResponse('wrong')


class DeleteServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        data = ServiceCatogarys.objects.get(id=id)
        data.delete()

        service_records = ServiceCatogarys.objects.all()
        context = {
            "services": service_records,
        }
        return render(request, "adminpages/Manage_Services.html", context)


class EditServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        service = get_object_or_404(ServiceCatogarys, id=id)
        return render(request, "adminpages/ServiceCatogry.html", {"record": service})

    def post(self, request, id):
        service = get_object_or_404(ServiceCatogarys, id=id)
        Name = request.POST.get("Name")
        Description = request.POST.get("Description")
        img = request.FILES.get("img")

        # Update the service category fields
        service.Name = Name
        service.Description = Description
        if img:
            service.img = img
        service.save()
        return HttpResponse("Update Successful")


# At the top of your views.py, make sure these are imported
from django.shortcuts import render, redirect
from django.contrib import messages

# ... your other imports and views


# In your views.py


class feedback_form(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request, worker_id=None):
        # Prepare the context dictionary
        context = {
            "workers": workers.objects.filter(acc_activation=True),
            "selected_worker": None,  # Initialize as None
        }

        # If a worker_id was passed in the URL, get that specific worker
        if worker_id:
            context["selected_worker"] = get_object_or_404(workers, id=worker_id)

        return render(request, "userpages/feedback_form.html", context)

    def post(self, request, **kwargs):
        # Your post logic remains the same
        Feedback.objects.create(
            Rating=int(request.POST.get("rating")),
            Description=request.POST.get("description"),
            User=request.user,
            Employ_id=request.POST.get("employ"),
            Date=datetime.now().date(),
        )
        messages.success(
            request, "Thank you! Your feedback has been successfully submitted."
        )
        # Redirect to the general feedback form after submission
        return redirect("feedback_form")


# At the top of your views.py, add this for calculations
from django.db.models import Avg, Count


# ... find your viewfeedbacks class and replace it with this ...
class viewfeedbacks(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        feedback_records = (
            Feedback.objects.select_related("User", "Employ__admin")
            .all()
            .order_by("-Date")
        )

        # Calculate sitewide statistics
        stats = feedback_records.aggregate(
            average_rating=Avg("Rating"), total_reviews=Count("id")
        )

        context = {
            "feedback_records": feedback_records,
            "average_rating": stats["average_rating"] or 0,
            "total_reviews": stats["total_reviews"] or 0,
        }
        return render(request, "adminpages/View_feedbacks.html", context)


class ViewRequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        request_records = ServiceRequests.objects.all()
        context = {
            "request_records": request_records,
        }
        return render(request, "adminpages/View_request.html", context)


class ViewColleagues(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        workers_records = workers.objects.all()
        context = {"workers_records": workers_records}
        return render(request, "workerpages/View_colleagues.html", context)

    # class WorkerViewRequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]


#     def get(self,request):
#         worker=request.user.id
#         print("worker_id",worker)

#         request_records=ServiceRequests.objects.all()
#         Response_record=Response.objects.all()
#         wo=workers.objects.filter(admin=worker)
#         asss = Response.objects.filter(assigned_worker__admin__id=worker)
#         print(asss)
#         # =Response_record.filter
#         context={
#             'request_records':request_records,
#             'Response_record':Response_record,
#         }
#         return render(request, 'workerpages/View_request.html', context)

# In your views.py


# In your views.py


class WorkerViewRequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        try:
            current_worker = workers.objects.get(admin=request.user)

            # --- THIS IS THE FIX ---
            # First, check if the worker is available
            if current_worker.avalability_status:
                # If they are available, find jobs that match their skills
                worker_designation = current_worker.designation
                available_requests = ServiceRequests.objects.filter(
                    status=False, service__Name=worker_designation
                ).order_by("-dateofrequest")
            else:
                # If they are not available, return an empty list of requests
                available_requests = ServiceRequests.objects.none()

        except workers.DoesNotExist:
            available_requests = []

        context = {
            "request_records": available_requests,
        }
        return render(request, "workerpages/View_request.html", context)


# At the top of your views.py, add this for calculations
from django.db.models import Avg, Count

# ... find your viewworkerfeedbacks class and replace it with this ...


class viewworkerfeedbacks(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        # Get the current worker
        current_worker = workers.objects.get(admin=request.user)

        # Filter feedbacks specifically for the logged-in worker
        feedback_records = Feedback.objects.filter(Employ=current_worker).order_by(
            "-Date"
        )

        # Calculate statistics
        stats = feedback_records.aggregate(
            average_rating=Avg("Rating"), total_reviews=Count("id")
        )

        context = {
            "feedback_records": feedback_records,
            "average_rating": stats["average_rating"]
            or 0,  # Default to 0 if no ratings
            "total_reviews": stats["total_reviews"] or 0,
        }
        return render(request, "workerpages/View_feedbacks.html", context)


# HomeServices_app/views.py

# ... your other imports and views


class ColleagueProfileView(LoginRequiredMixin, View):
    """
    This view displays the public profile of a specific colleague (worker).
    """

    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, pk):
        # Get the specific worker using the primary key (pk) from the URL
        colleague_data = get_object_or_404(workers, pk=pk)

        context = {
            "data": colleague_data,
        }
        return render(request, "workerpages/colleague_profile.html", context)


class viewrequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        worker = request.user
        print("worker_id", worker)
        request_records = ServiceRequests.objects.all()
        context = {
            "request_records": request_records,
        }
        return render(request, "adminpages/View_request.html", context)


# In your views.py
from django.db import transaction  # Make sure to import this at the top


class acceptrequest(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, action, id):
        # Use a database transaction to ensure the check and update are atomic
        try:
            with transaction.atomic():
                # 1. Find the service request the worker wants to accept
                service_request = ServiceRequests.objects.select_for_update().get(id=id)

                # 2. CRITICAL: Check if the request is still available (status is False)
                if service_request.status == False:
                    # 3. If it's available, claim it
                    service_request.status = True  # Mark as "assigned"
                    service_request.save()

                    # 4. Create the Response object linking this worker to the request
                    current_worker = workers.objects.get(admin=request.user)
                    Response.objects.create(
                        requests=service_request,
                        assigned_worker=current_worker,
                        status=False,  # status=False on Response means "In Progress"
                    )

                    messages.success(
                        request,
                        f"Job '{service_request.service.Name}' has been successfully accepted!",
                    )
                else:
                    # 5. If another worker already took it, show an error message
                    messages.error(
                        request,
                        "Sorry, this job has already been taken by another provider.",
                    )

        except ServiceRequests.DoesNotExist:
            messages.error(request, "This service request no longer exists.")

        # Always redirect back to the list of available jobs
        return redirect("WorkerViewRequests")


class viewresponse(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        Response_records = Response.objects.all()
        context = {
            "Response_records": Response_records,
        }
        return render(request, "adminpages/view_response.html", context)


# In your views.py


class workerviewresponse(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request):
        worker_instance = get_object_or_404(workers, admin=request.user)

        # --- THIS IS THE FIX ---
        # Order by status (False comes first), then by the most recent date
        assigned_responses = Response.objects.filter(
            assigned_worker=worker_instance
        ).order_by("status", "-Date")
        # --- END OF FIX ---

        context = {
            "Response_records": assigned_responses,
        }
        return render(request, "workerpages/viewpending_task.html", context)

    def test_func(self):
        return self.request.user.is_staff and not self.request.user.is_superuser


class Viewappointment_history(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        # Get the logged-in user's ID
        user_id = request.user.id

        # Query request data for the logged-in user
        requests_data = ServiceRequests.objects.filter(user__admin_id=user_id)

        # Initialize lists to store request and response data
        request_list = []
        response_list = []

        for request_data in requests_data:
            # Check if a response exists for the request
            response = Response.objects.filter(requests=request_data).first()

            if response:
                # If a response exists, add it to the response list
                response_list.append(response)
            else:
                # If no response exists, add the request to the request list
                request_list.append(request_data)

        context = {
            "requests": request_list,
            "responses": response_list,
        }

        return render(request, "userpages/appointment_history.html", context)


# In your views.py file

class CancelRequest(LoginRequiredMixin, View):
    login_url = 'login'

    # FIX: Changed this method from 'get' to 'post'
    def post(self, request, id):
        try:
            # Logic for an admin cancelling a request
            if request.user.is_superuser:
                service_request = get_object_or_404(ServiceRequests, id=id)
                redirect_url = 'ViewRequests'
            # Logic for a regular user cancelling their own request
            else:
                user_profile = get_object_or_404(users, admin=request.user)
                service_request = get_object_or_404(ServiceRequests, id=id, user=user_profile)
                redirect_url = 'Viewappointment_history'
            
            # Delete the request and show a success message
            service_request.delete()
            messages.success(request, "The service request has been successfully cancelled.")
        
        except ServiceRequests.DoesNotExist:
            messages.error(request, "The request you tried to cancel does not exist.")
            redirect_url = 'Viewappointment_history' # Default redirect

        return redirect(redirect_url)


# In your views.py


class AssignWorker(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, id):
        req = ServiceRequests.objects.get(id=id)
        service = req.service.Name

        # --- THIS IS THE FIX ---
        # Filter for workers who have the right designation AND are available
        workers_records = workers.objects.filter(
            designation=service,
            avalability_status=True,  # Only show workers who are available
        )

        context = {
            "req": req,
            "workers_records": workers_records,
        }
        return render(request, "adminpages/assign_worker.html", context)

    def post(self, request, id):
        ServiceRequests.objects.filter(id=id).update(status=True)
        worker = request.POST.get("assigned_worker")
        req = ServiceRequests.objects.get(id=id)
        print(worker)
        assigned_worker = workers.objects.get(id=worker)
        print(assigned_worker)
        worker_id = workers.objects.get(id=worker)
        response = Response.objects.create(
            requests=req, assigned_worker=worker_id, status=False
        )
        return HttpResponseRedirect("/viewresponse")


class userprofile(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):
        id = request.user.id
        data = users.objects.get(admin=id)
        context = {
            "data": data,
        }
        return render(request, "userpages/user_profile.html", context)


class workerprofile(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request):

        user = request.user.id

        data = workers.objects.get(admin=user)
        context = {
            "data": data,
        }
        return render(request, "workerpages/worker_profile.html", context)


class markcompleted(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, action, id):
        try:
            if action == "completed":
                Response.objects.filter(id=id, status=False).update(status=True)
                print("Response status updated successfully.")
            else:
                print("Action not 'completed' or status is already True.")

            return HttpResponseRedirect("/WorkerpendingTask")
        except Response.DoesNotExist:
            print(f"Response with id {id} does not exist.")
            return HttpResponse(status=404)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return HttpResponse(status=500)


class reject(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH["ROOT"]

    def get(self, request, action, id):
        response_record = Response.objects.get(id=id)
        request_record = response_record.requests
        r_id = request_record.id
        ServiceRequests.objects.filter(id=r_id).update(status=False)

        response_record.delete()
        return HttpResponseRedirect("/WorkerpendingTask")
