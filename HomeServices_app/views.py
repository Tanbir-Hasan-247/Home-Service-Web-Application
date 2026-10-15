import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import random
import re
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from .forms import stateform
from .models import (
    ChatMessage,
    City,
    Country,
    Feedback,
    Notification,
    Response,
    ServiceCatogarys,
    ServiceAddOn,
    ServiceRequests,
    State,
    WithdrawalRequest,
    users,
    workers,
)


class Commenlib:
    def __init__(self):
        self.DEFAULT_REDIRECT_PATH = {"ROOT": "/"}


common_lib = Commenlib()


# ==============================================================================
# Role-based Mixins
# ==============================================================================

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Ensures that only superusers (administrators) can access the view."""
    login_url = "login"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.login_url)
        messages.error(self.request, "Access restricted to administrators.")
        return redirect("index")


class WorkerRequiredMixin(UserPassesTestMixin):
    """Ensures that only service providers (workers) can access the view."""
    login_url = "login"

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and not self.request.user.is_superuser
            and workers.objects.filter(admin=self.request.user).exists()
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.login_url)
        messages.error(self.request, "Access restricted to service providers.")
        return redirect("index")


def send_notification(user, title, message, link="", notification_type="system"):
    """Creates an in-app notification for the user."""
    if user:
        try:
            return Notification.objects.create(
                user=user,
                title=title,
                message=message,
                link=link or "",
                notification_type=notification_type,
            )
        except Exception:
            pass
    return None



# ==============================================================================
# Authentication & Registration Views
# ==============================================================================

class Login(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect("admmin_home")
            elif request.user.is_staff:
                return redirect("workers_home")
            else:
                return redirect("index")
        return render(request, "login.html")

    def post(self, request):
        username_or_email = request.POST.get("uname", "").strip()
        password = request.POST.get("psw", "")

        # Try direct username authentication
        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            # Fallback to case-insensitive username or email matching
            matched_user = User.objects.filter(
                Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
            ).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect("admmin_home")
            elif user.is_staff:
                return redirect("workers_home")
            else:
                return redirect("index")
        else:
            return render(request, "login.html", {"error_msg": "Invalid email/username or password."})


def logout_view(request):
    logout(request)
    return redirect("login")


def signup_selection_view(request):
    """Renders the page where the user chooses Customer or Service Provider signup."""
    return render(request, "signup_selection.html")


class User_Register(View):
    template_name = "user_register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("index")
        return render(request, self.template_name)

    def post(self, request):
        first_name = request.POST.get("firstname", "").strip()
        last_name = request.POST.get("lastname", "").strip()
        email = request.POST.get("email", "").strip().lower()
        contact_number = request.POST.get("contactnumber", "").strip()
        address = request.POST.get("address", "").strip()
        profile_pics = request.FILES.get("profile_pic")
        gender = request.POST.get("gender", "").strip()
        password = request.POST.get("password", "")
        cpassword = request.POST.get("cpassword", "")

        form_data = {
            "firstname": first_name,
            "lastname": last_name,
            "email": email,
            "contactnumber": contact_number,
            "address": address,
            "gender": gender,
        }

        if password != cpassword:
            messages.error(request, "Passwords do not match!")
            return render(request, self.template_name, {"form_data": form_data})

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, self.template_name, {"form_data": form_data})

        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            messages.error(request, "An account with this email address already exists. Please log in or use a different email.")
            return render(request, self.template_name, {"form_data": form_data})

        try:
            with transaction.atomic():
                new_user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                users.objects.create(
                    admin=new_user,
                    Address=address,
                    gender=gender,
                    contact_number=contact_number,
                    profile_pic=profile_pics,
                )

            messages.success(request, "Registration successful! You can now log in.")
            return redirect("login")

        except Exception as e:
            messages.error(request, f"An unexpected error occurred during registration: {e}")
            return render(request, self.template_name, {"form_data": form_data})


class Worker_Register(View):
    template_name = "workers_registration.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("index")
        designations = ServiceCatogarys.objects.all().order_by("Name")
        cities = City.objects.all().order_by("name")
        context = {
            "designations": designations,
            "cities": cities,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        first_name = request.POST.get("firstname", "").strip()
        last_name = request.POST.get("lastname", "").strip()
        email = request.POST.get("email", "").strip().lower()
        contact_number = request.POST.get("contactnumber", "").strip()
        dob = request.POST.get("dob")
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        selected_service_areas = request.POST.getlist("service_areas")
        gender = request.POST.get("gender", "").strip()
        designation = request.POST.get("designation", "").strip()
        profile_pics = request.FILES.get("profile_pic")
        password = request.POST.get("password", "")
        cpassword = request.POST.get("cpassword", "")

        designations = ServiceCatogarys.objects.all().order_by("Name")
        cities = City.objects.all().order_by("name")

        context = {
            "designations": designations,
            "cities": cities,
            "form_data": {
                "firstname": first_name,
                "lastname": last_name,
                "email": email,
                "contactnumber": contact_number,
                "dob": dob,
                "address": address,
                "city": city,
                "gender": gender,
                "designation": designation,
                "selected_service_areas": [int(x) for x in selected_service_areas if x.isdigit()],
            },
        }

        if password != cpassword:
            messages.error(request, "Passwords do not match!")
            return render(request, self.template_name, context)

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, self.template_name, context)

        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            messages.error(request, "An account with this email address already exists. Please log in or use a different email.")
            return render(request, self.template_name, context)

        if not designation:
            messages.error(request, "Please select your primary service designation.")
            return render(request, self.template_name, context)

        if not selected_service_areas:
            messages.error(request, "Please select at least one service coverage area (city) where you will accept jobs.")
            return render(request, self.template_name, context)

        try:
            with transaction.atomic():
                new_user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_staff=True,
                    is_superuser=False,
                )

                primary_city_obj = City.objects.filter(id__in=selected_service_areas).first()
                worker_city_text = city if city else (primary_city_obj.name if primary_city_obj else "")

                worker_instance = workers.objects.create(
                    admin=new_user,
                    contact_number=contact_number,
                    dob=dob if dob else None,
                    Address=address,
                    city=worker_city_text,
                    gender=gender,
                    designation=designation,
                    profile_pic=profile_pics,
                    acc_activation=False,
                    avalability_status=True,
                )

                worker_instance.service_areas.set(selected_service_areas)

            messages.success(
                request,
                "Worker registration successful! Your account has been registered with your selected service coverage areas and is awaiting admin verification. You can now log in.",
            )
            return redirect("login")

        except Exception as e:
            messages.error(request, f"An unexpected error occurred during registration: {e}")
            return render(request, self.template_name, context)


# ==============================================================================
# Public Website Views
# ==============================================================================

class home(View):
    def get(self, request):
        services = ServiceCatogarys.objects.all()
        feedbacks = Feedback.objects.select_related("User", "Employ__admin").all().order_by("-Date")[:6]
        all_services = list(services)
        sample_size = min(6, len(all_services))
        selected_services = random.sample(all_services, sample_size) if all_services else []
        context = {
            "services": services,
            "feedbacks": feedbacks,
            "selected_services": selected_services,
        }
        return render(request, "userpages/index.html", context)


class about(View):
    def get(self, request):
        return render(request, "userpages/about.html")


class services(View):
    def get(self, request):
        all_services = ServiceCatogarys.objects.all().order_by("Name")
        feedbacks = Feedback.objects.select_related("User").all().order_by("-Date")[:6]
        context = {
            "services": all_services,
            "feedbacks": feedbacks,
        }
        return render(request, "userpages/service.html", context)


class contact(View):
    """Informational contact page accessible to all site visitors."""
    def get(self, request):
        return render(request, "userpages/contact.html")

    def post(self, request):
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if not name or not email or not subject or not message:
            messages.error(request, "Please fill in all fields before sending your message.")
            return redirect("contact")

        messages.success(
            request,
            f"Thank you, {name}! Your message regarding '{subject}' has been received. Our team will contact you at {email} shortly."
        )
        return redirect("contact")


# ==============================================================================
# Customer Views
# ==============================================================================

class userprofile(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request):
        if request.user.is_superuser:
            return redirect("admmin_home")
        if request.user.is_staff:
            return redirect("workerprofile")

        user_profile, _ = users.objects.get_or_create(admin=request.user)
        context = {
            "data": user_profile,
        }
        return render(request, "userpages/user_profile.html", context)


class EditProfileView(LoginRequiredMixin, View):
    template_name = "userpages/edit_profile.html"
    login_url = "login"

    def get(self, request):
        if request.user.is_superuser:
            return redirect("admmin_home")
        if request.user.is_staff:
            return redirect("edit_worker_profile")

        user_profile, _ = users.objects.get_or_create(admin=request.user)
        return render(request, self.template_name, {"data": user_profile})

    def post(self, request):
        if request.user.is_superuser:
            return redirect("admmin_home")
        if request.user.is_staff:
            return redirect("edit_worker_profile")

        user_profile, _ = users.objects.get_or_create(admin=request.user)

        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.save()

        user_profile.contact_number = request.POST.get("contact_number", "").strip()
        user_profile.Address = request.POST.get("address", "").strip()
        user_profile.gender = request.POST.get("gender", "").strip()

        if "profile_pic" in request.FILES:
            user_profile.profile_pic = request.FILES["profile_pic"]

        user_profile.save()
        messages.success(request, "Your profile has been updated successfully!")
        return redirect("userprofile")


class DeleteProfileView(LoginRequiredMixin, View):
    login_url = "login"

    def post(self, request):
        user_to_delete = request.user
        logout(request)
        user_to_delete.delete()
        return redirect("index")


class bookservice(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request, id):
        if request.user.is_superuser:
            messages.warning(request, "Administrators cannot book services.")
            return redirect("services")
        if request.user.is_staff:
            messages.warning(request, "Service providers cannot book services.")
            return redirect("services")

        service = get_object_or_404(ServiceCatogarys, id=id)
        city = City.objects.all().order_by("name")
        user_profile = users.objects.filter(admin=request.user).first()
        addons = service.addons.filter(is_active=True)
        context = {
            "services": service,
            "city": city,
            "user_profile": user_profile,
            "addons": addons,
        }
        return render(request, "userpages/servicebook.html", context)

    def post(self, request, id):
        if request.user.is_superuser or request.user.is_staff:
            messages.warning(request, "Only customer accounts can book services.")
            return redirect("services")

        service_obj = get_object_or_404(ServiceCatogarys, id=id)
        user_profile, _ = users.objects.get_or_create(admin=request.user)

        problem_description = (request.POST.get("Problem_Description") or request.POST.get("des") or "").strip()
        address = (request.POST.get("Address") or request.POST.get("address") or "").strip()
        city_id = request.POST.get("city")
        pin = (request.POST.get("Pincode") or request.POST.get("pincode") or request.POST.get("pin") or "").strip()
        house_no = (request.POST.get("House_No") or request.POST.get("house_no") or "").strip()
        landmark = request.POST.get("landmark", "").strip()
        contact_number = (request.POST.get("contact") or request.POST.get("contact_number") or "").strip()

        if not problem_description or not address or not city_id or not pin or not house_no or not contact_number:
            messages.error(request, "Please fill in all required fields (problem description, address, city, pincode, house number, and contact number).")
            return redirect("bookservice", id=id)

        city_obj = get_object_or_404(City, id=city_id)
        lat_raw = request.POST.get("latitude", "").strip()
        lng_raw = request.POST.get("longitude", "").strip()
        try:
            latitude = float(lat_raw) if lat_raw else None
            longitude = float(lng_raw) if lng_raw else None
        except (ValueError, TypeError):
            latitude, longitude = None, None

        # Process optional service add-ons
        addon_ids = request.POST.getlist("addons")
        selected_addons = ServiceAddOn.objects.filter(id__in=addon_ids, service=service_obj, is_active=True)
        addons_total = sum((a.price for a in selected_addons), Decimal("0.00"))

        sr = ServiceRequests.objects.create(
            user=user_profile,
            Problem_Description=problem_description,
            service=service_obj,
            Address=address,
            city=city_obj,
            pin=pin,
            House_No=house_no,
            landmark=landmark,
            contact=contact_number,
            latitude=latitude,
            longitude=longitude,
            addons_total=addons_total,
            status=False,
        )
        if selected_addons.exists():
            sr.selected_addons.set(selected_addons)

        # Notify all admins of the new request
        for admin_user in User.objects.filter(is_superuser=True):
            send_notification(
                admin_user,
                "New Booking Request",
                f"New customer request for '{service_obj.Name}' in {city_obj.name} by {request.user.get_full_name() or request.user.username}.",
                link=reverse("ViewRequests"),
                notification_type="booking"
            )

        # Notify available workers who cover this city and service
        matching_workers = workers.objects.filter(
            designation=service_obj.Name,
            acc_activation=True,
            avalability_status=True,
            service_areas=city_obj
        ).select_related("admin")
        for w in matching_workers:
            send_notification(
                w.admin,
                "New Job Available!",
                f"New {service_obj.Name} job requested in your coverage area ({city_obj.name}). Tap to view and accept.",
                link=reverse("WorkerViewRequests"),
                notification_type="booking"
            )

        messages.success(
            request,
            f"Your request for '{service_obj.Name}' has been successfully submitted! We have notified nearby technicians.",
        )
        return redirect("Viewappointment_history")


class Viewappointment_history(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request):
        if request.user.is_superuser:
            return redirect("ViewRequests")
        if request.user.is_staff:
            return redirect("WorkerpendingTask")

        user_profile = users.objects.filter(admin=request.user).first()
        if not user_profile:
            return render(request, "userpages/appointment_history.html", {"requests": [], "responses": []})

        requests_data = (
            ServiceRequests.objects.filter(user=user_profile)
            .select_related("service", "city")
            .prefetch_related("selected_addons")
            .order_by("-dateofrequest")
        )

        # Single batch query to eliminate N+1 query loop
        responses_by_req = {
            resp.requests_id: resp
            for resp in Response.objects.filter(requests__in=requests_data)
            .select_related("assigned_worker__admin", "requests__service", "requests__city")
            .prefetch_related("requests__selected_addons")
        }

        request_list = []
        response_list = []

        for req in requests_data:
            if req.id in responses_by_req:
                response_list.append(responses_by_req[req.id])
            else:
                request_list.append(req)

        context = {
            "requests": request_list,
            "responses": response_list,
        }
        return render(request, "userpages/appointment_history.html", context)


class CancelRequest(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request, id):
        return self._cancel(request, id)

    def post(self, request, id):
        return self._cancel(request, id)

    def _cancel(self, request, id):
        if request.user.is_superuser:
            service_request = ServiceRequests.objects.filter(id=id).first()
            redirect_url = "ViewRequests"
        else:
            user_profile = users.objects.filter(admin=request.user).first()
            if not user_profile:
                messages.error(request, "User profile not found.")
                return redirect("Viewappointment_history")
            service_request = ServiceRequests.objects.filter(id=id, user=user_profile).first()
            redirect_url = "Viewappointment_history"

        if service_request:
            service_request.delete()
            messages.success(request, "The service request has been successfully cancelled.")
        else:
            messages.error(request, "The request you tried to cancel does not exist or has already been removed.")

        return redirect(redirect_url)


class feedback_form(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request, worker_id=None):
        if request.user.is_staff and not request.user.is_superuser:
            messages.info(request, "Service providers cannot submit customer feedback.")
            return redirect("workers_home")

        context = {
            "workers": workers.objects.filter(acc_activation=True).select_related("admin"),
            "selected_worker": None,
        }

        if worker_id:
            context["selected_worker"] = get_object_or_404(workers, id=worker_id)

        return render(request, "userpages/feedback_form.html", context)

    def post(self, request, **kwargs):
        rating = request.POST.get("rating")
        description = request.POST.get("description", "").strip()
        employ_id = request.POST.get("employ") or kwargs.get("worker_id")

        if not rating or not employ_id or not description:
            messages.error(request, "Please fill in all required fields.")
            if kwargs.get("worker_id"):
                return redirect("feedback_form_for_worker", worker_id=kwargs.get("worker_id"))
            return redirect("feedback_form")

        try:
            worker = workers.objects.get(id=employ_id)
            Feedback.objects.create(
                Rating=int(rating),
                Description=description,
                User=request.user,
                Employ=worker,
                Date=datetime.now().date(),
            )
            messages.success(
                request, "Thank you! Your feedback has been successfully submitted."
            )
            return redirect("Viewappointment_history")
        except Exception as e:
            messages.error(request, f"Failed to submit feedback: {e}")
            if kwargs.get("worker_id"):
                return redirect("feedback_form_for_worker", worker_id=kwargs.get("worker_id"))
            return redirect("feedback_form")


# ==============================================================================
# Worker Views
# ==============================================================================

class workers_home(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request):
        worker_instance = get_object_or_404(workers, admin=request.user)
        my_responses = Response.objects.filter(assigned_worker=worker_instance).select_related("requests__service", "requests__user__admin")
        my_feedbacks = Feedback.objects.filter(Employ=worker_instance).order_by("Date")

        stats = my_feedbacks.aggregate(avg=Avg("Rating"))
        rating_counts = my_feedbacks.values("Rating").annotate(count=Count("Rating")).order_by("-Rating")
        ratings_data = {str(i): 0 for i in range(1, 6)}
        for item in rating_counts:
            ratings_data[str(item["Rating"])] = item["count"]

        rating_trend_labels = []
        rating_trend_data = []
        total_rating_sum = 0
        review_count = 0

        for fb in my_feedbacks:
            review_count += 1
            total_rating_sum += fb.Rating
            current_average = total_rating_sum / review_count
            rating_trend_labels.append(f"Review #{review_count}")
            rating_trend_data.append(round(current_average, 2))

        total_earnings = my_responses.filter(payment_status="Paid").aggregate(total=Sum("worker_earning"))["total"] or 0.00
        pending_earnings = my_responses.filter(status=True, payment_status="Pending").aggregate(total=Sum("worker_earning"))["total"] or 0.00

        context = {
            "completed_jobs": my_responses.filter(status=True).count(),
            "active_jobs": my_responses.filter(status=False).count(),
            "total_reviews": my_feedbacks.count(),
            "average_rating": stats["avg"] or 0,
            "total_earnings": total_earnings,
            "pending_earnings": pending_earnings,
            "recent_jobs": my_responses.filter(status=False).order_by("-Date")[:3],
            "ratings_chart_labels": json.dumps([f"{star} Star" for star in ratings_data.keys()]),
            "ratings_chart_data": json.dumps(list(ratings_data.values())),
            "rating_trend_labels": json.dumps(rating_trend_labels),
            "rating_trend_data": json.dumps(rating_trend_data),
        }
        return render(request, "workerpages/Workerhompage.html", context)


class workerprofile(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request):
        if request.user.is_superuser:
            return redirect("admmin_home")
        if not request.user.is_staff:
            return redirect("userprofile")

        worker = get_object_or_404(workers, admin=request.user)
        context = {
            "data": worker,
        }
        return render(request, "workerpages/worker_profile.html", context)


class EditWorkerProfileView(LoginRequiredMixin, WorkerRequiredMixin, View):
    template_name = "workerpages/edit_worker_profile.html"

    def get(self, request):
        worker_profile = get_object_or_404(workers, admin=request.user)
        cities = City.objects.all().order_by("name")
        selected_area_ids = list(worker_profile.service_areas.values_list("id", flat=True))
        context = {
            "data": worker_profile,
            "cities": cities,
            "selected_area_ids": selected_area_ids,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        worker_profile = get_object_or_404(workers, admin=request.user)

        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.save()

        worker_profile.contact_number = request.POST.get("contact_number", "").strip()
        dob = request.POST.get("dob")
        worker_profile.dob = dob if dob else None
        worker_profile.Address = request.POST.get("Address", "").strip()
        worker_profile.city = request.POST.get("city", "").strip()
        worker_profile.gender = request.POST.get("gender", "").strip()

        if "profile_pic" in request.FILES:
            worker_profile.profile_pic = request.FILES["profile_pic"]

        selected_areas = request.POST.getlist("service_areas")
        if not selected_areas:
            messages.error(request, "Please select at least one service coverage area (city) where you accept jobs.")
            return redirect("edit_worker_profile")

        worker_profile.service_areas.set(selected_areas)
        worker_profile.save()
        messages.success(request, "Your profile and service coverage areas have been updated successfully!")
        return redirect("workerprofile")


class DeleteWorkerProfileView(LoginRequiredMixin, WorkerRequiredMixin, View):
    def post(self, request):
        user_to_delete = request.user
        logout(request)
        user_to_delete.delete()
        return redirect("index")


class ToggleAvailabilityView(LoginRequiredMixin, WorkerRequiredMixin, View):
    def post(self, request):
        worker = get_object_or_404(workers, admin=request.user)
        worker.avalability_status = not worker.avalability_status
        worker.save()
        status_text = "Available" if worker.avalability_status else "Unavailable"
        messages.success(request, f"Availability status set to: {status_text}")
        return redirect("workerprofile")

    def get(self, request):
        return self.post(request)


class ViewColleagues(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request):
        workers_records = workers.objects.filter(acc_activation=True).exclude(admin=request.user).select_related("admin").order_by("admin__first_name")
        context = {"workers_records": workers_records}
        return render(request, "workerpages/View_colleagues.html", context)


class ColleagueProfileView(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request, pk):
        colleague_data = get_object_or_404(workers, pk=pk)
        context = {
            "data": colleague_data,
        }
        return render(request, "workerpages/colleague_profile.html", context)


class WorkerViewRequests(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request):
        try:
            current_worker = workers.objects.get(admin=request.user)
            if not current_worker.acc_activation:
                messages.warning(request, "Your account is awaiting administrator verification. You will be able to accept jobs once verified.")
                available_requests = ServiceRequests.objects.none()
            elif current_worker.avalability_status:
                worker_designation = current_worker.designation
                worker_areas = current_worker.service_areas.all()

                if worker_areas.exists():
                    available_requests = (
                        ServiceRequests.objects.filter(
                            status=False,
                            service__Name__iexact=worker_designation,
                            city__in=worker_areas,
                        )
                        .select_related("user__admin", "service", "city")
                        .prefetch_related("selected_addons")
                        .distinct()
                        .order_by("-dateofrequest")
                    )
                else:
                    available_requests = (
                        ServiceRequests.objects.filter(
                            status=False,
                            service__Name__iexact=worker_designation,
                            city__name__iexact=current_worker.city,
                        )
                        .select_related("user__admin", "service", "city")
                        .prefetch_related("selected_addons")
                        .order_by("-dateofrequest")
                    )
            else:
                messages.info(request, "You are currently set to Unavailable. Toggle your availability in your profile to accept jobs.")
                available_requests = ServiceRequests.objects.none()
        except workers.DoesNotExist:
            available_requests = ServiceRequests.objects.none()

        context = {
            "request_records": available_requests,
            "worker": current_worker if 'current_worker' in locals() else None,
        }
        return render(request, "workerpages/View_request.html", context)


class viewworkerfeedbacks(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request):
        current_worker = get_object_or_404(workers, admin=request.user)
        feedback_records = Feedback.objects.filter(Employ=current_worker).select_related("User").order_by("-Date")

        stats = feedback_records.aggregate(
            average_rating=Avg("Rating"), total_reviews=Count("id")
        )

        context = {
            "feedback_records": feedback_records,
            "average_rating": stats["average_rating"] or 0,
            "total_reviews": stats["total_reviews"] or 0,
        }
        return render(request, "workerpages/View_feedbacks.html", context)


class workerviewresponse(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request):
        worker_instance = get_object_or_404(workers, admin=request.user)
        assigned_responses = (
            Response.objects.filter(assigned_worker=worker_instance)
            .select_related("requests__service", "requests__user__admin", "requests__city")
            .prefetch_related("requests__selected_addons")
            .order_by("status", "-Date")
        )

        context = {
            "Response_records": assigned_responses,
        }
        return render(request, "workerpages/viewpending_task.html", context)


class acceptrequest(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request, action, id):
        current_worker = get_object_or_404(workers, admin=request.user)
        if not current_worker.acc_activation:
            messages.error(request, "Your account must be verified by an admin before you can accept jobs.")
            return redirect("WorkerViewRequests")

        try:
            with transaction.atomic():
                service_request = ServiceRequests.objects.select_for_update().get(id=id)

                # STRICT AREA RESTRICTION: Worker cannot accept jobs outside their registered service areas
                if not current_worker.serves_city(service_request.city):
                    messages.error(
                        request,
                        f"Cannot accept job: The request location '{service_request.city.name}' is outside your registered service area(s) ({current_worker.get_service_areas_display()})."
                    )
                    return redirect("WorkerViewRequests")

                if not service_request.status:
                    service_request.status = True
                    service_request.save()

                    resp = Response.objects.create(
                        requests=service_request,
                        assigned_worker=current_worker,
                        status=False,
                        job_status="Accepted",
                    )
                    send_notification(
                        service_request.user.admin,
                        "Technician Assigned & Accepted!",
                        f"Technician {current_worker.admin.get_full_name()} accepted your job for '{service_request.service.Name}'. Phone: {current_worker.contact_number}.",
                        link=reverse("Viewappointment_history"),
                        notification_type="status",
                    )
                    messages.success(
                        request,
                        f"Job '{service_request.service.Name}' has been successfully accepted! Customer Address: {service_request.House_No}, {service_request.Address}, {service_request.city.name}.",
                    )
                else:
                    messages.error(
                        request,
                        "Sorry, this job has already been taken by another provider.",
                    )
        except ServiceRequests.DoesNotExist:
            messages.error(request, "This service request no longer exists.")

        return redirect("WorkerViewRequests")


class UpdateJobStatusView(LoginRequiredMixin, WorkerRequiredMixin, View):
    """Allows worker to update job status timeline: on_the_way, in_progress, cancel."""
    def get(self, request, id, new_status):
        worker = get_object_or_404(workers, admin=request.user)
        response_obj = get_object_or_404(Response, id=id, assigned_worker=worker)

        status_clean = new_status.lower().replace(" ", "_").replace("-", "_")

        if status_clean in ["on_the_way", "ontheway"]:
            response_obj.job_status = "On the Way"
            response_obj.on_the_way_at = timezone.now()
            response_obj.save()
            send_notification(
                response_obj.requests.user.admin,
                "Technician On The Way!",
                f"{worker.admin.get_full_name()} has started heading to your location for '{response_obj.requests.service.Name}'.",
                link=reverse("Viewappointment_history"),
                notification_type="status",
            )
            messages.success(request, f"Status updated to 'On the Way' for {response_obj.requests.service.Name}.")
        elif status_clean in ["in_progress", "inprogress"]:
            response_obj.job_status = "In Progress"
            response_obj.in_progress_at = timezone.now()
            response_obj.save()
            send_notification(
                response_obj.requests.user.admin,
                "Service In Progress",
                f"{worker.admin.get_full_name()} has arrived at your address and started working on '{response_obj.requests.service.Name}'.",
                link=reverse("Viewappointment_history"),
                notification_type="status",
            )
            messages.success(request, f"Status updated to 'In Progress'. Perform the service carefully.")
        elif status_clean in ["cancel", "cancelled"]:
            req = response_obj.requests
            req.status = False
            req.save()
            send_notification(
                req.user.admin,
                "Job Reopened",
                f"Your provider was unable to attend. The job '{req.service.Name}' has been placed back in the open requests pool.",
                link=reverse("Viewappointment_history"),
                notification_type="status",
            )
            response_obj.delete()
            messages.info(request, "Job cancelled and returned to available requests.")
        else:
            messages.warning(request, "Unknown status action.")

        return redirect("WorkerpendingTask")


class UpdateWorkerLocationView(LoginRequiredMixin, WorkerRequiredMixin, View):
    """API for worker to post their current GPS location while heading to customer."""
    def post(self, request, id):
        worker = get_object_or_404(workers, admin=request.user)
        response_obj = get_object_or_404(Response, id=id, assigned_worker=worker)

        try:
            if request.content_type == "application/json":
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST
            lat = float(data.get("latitude"))
            lng = float(data.get("longitude"))
        except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
            return JsonResponse({"status": "error", "message": "Invalid coordinates"}, status=400)

        response_obj.worker_latitude = Decimal(str(round(lat, 6)))
        response_obj.worker_longitude = Decimal(str(round(lng, 6)))
        response_obj.last_location_update = timezone.now()
        response_obj.save()

        return JsonResponse({
            "status": "success",
            "worker_lat": float(response_obj.worker_latitude),
            "worker_lng": float(response_obj.worker_longitude),
            "updated_at": response_obj.last_location_update.strftime("%I:%M:%S %p")
        })


class GetLiveLocationView(LoginRequiredMixin, View):
    """API for customer / worker to poll technician live GPS location and ETA."""
    def get(self, request, id):
        import math
        response_obj = get_object_or_404(
            Response.objects.select_related("requests__user__admin", "assigned_worker__admin", "requests__service"),
            id=id
        )

        is_customer = (response_obj.requests.user.admin == request.user)
        is_worker = (response_obj.assigned_worker.admin == request.user)
        is_admin = request.user.is_superuser

        if not (is_customer or is_worker or is_admin):
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

        cust_lat = float(response_obj.requests.latitude or 23.8103)
        cust_lng = float(response_obj.requests.longitude or 90.4125)

        if response_obj.worker_latitude and response_obj.worker_longitude:
            worker_lat = float(response_obj.worker_latitude)
            worker_lng = float(response_obj.worker_longitude)
        else:
            # Deterministic simulation near customer destination (approaching ~1.5 km away)
            worker_lat = round(cust_lat - 0.0115, 6)
            worker_lng = round(cust_lng - 0.0085, 6)

        R = 6371.0
        dlat = math.radians(cust_lat - worker_lat)
        dlon = math.radians(cust_lng - worker_lng)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(worker_lat)) * math.cos(math.radians(cust_lat)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = round(R * c * 1.35, 1)

        eta_minutes = max(2, int((distance_km / 22.0) * 60))

        return JsonResponse({
            "status": "success",
            "job_status": response_obj.job_status,
            "worker_name": response_obj.assigned_worker.admin.get_full_name() or response_obj.assigned_worker.admin.username,
            "worker_phone": response_obj.assigned_worker.contact_number,
            "worker_designation": response_obj.assigned_worker.designation,
            "worker_lat": worker_lat,
            "worker_lng": worker_lng,
            "customer_lat": cust_lat,
            "customer_lng": cust_lng,
            "customer_address": f"{response_obj.requests.House_No}, {response_obj.requests.Address}",
            "distance_km": distance_km,
            "eta_minutes": eta_minutes,
            "formatted_eta": f"{eta_minutes} mins",
            "last_update": response_obj.last_location_update.strftime("%I:%M:%S %p") if response_obj.last_location_update else "Live (GPS Active)"
        })


class markcompleted(LoginRequiredMixin, WorkerRequiredMixin, View):
    def post(self, request, action, id):
        return self._complete(request, action, id)

    def get(self, request, action, id):
        return self._complete(request, action, id)

    def _complete(self, request, action, id):
        current_worker = get_object_or_404(workers, admin=request.user)
        response_record = Response.objects.filter(id=id, assigned_worker=current_worker).first()

        if not response_record:
            messages.error(request, "Task not found or not assigned to you.")
            return redirect("WorkerpendingTask")

        if action.lower() == "completed":
            hours_raw = request.POST.get("hours_worked") or request.GET.get("hours") or "1.0"
            try:
                hours = max(0.5, float(hours_raw))
            except (ValueError, TypeError):
                hours = 1.0

            response_record.calculate_bill(hours)
            response_record.status = True
            response_record.job_status = "Completed"
            response_record.completed_at = timezone.now()
            response_record.save()

            send_notification(
                response_record.requests.user.admin,
                "Service Completed - Bill Ready",
                f"Your service '{response_record.requests.service.Name}' is completed ({response_record.hours_worked} hrs). Total bill: ৳{response_record.total_amount}. Click to pay.",
                link=reverse("process_payment", args=[response_record.id]),
                notification_type="payment",
            )

            messages.success(
                request,
                f"Task '{response_record.requests.service.Name}' marked as completed! "
                f"Logged {response_record.hours_worked} hrs. "
                f"Total bill: ৳{response_record.total_amount} (Your 90% payout: ৳{response_record.worker_earning}, Platform 10% commission: ৳{response_record.admin_commission})."
            )
        else:
            messages.warning(request, "Action not recognized.")

        return redirect("WorkerpendingTask")


class ProcessPaymentView(LoginRequiredMixin, View):
    login_url = "login"

    def get(self, request, response_id):
        if request.user.is_superuser:
            response_record = get_object_or_404(Response, id=response_id)
        else:
            response_record = get_object_or_404(
                Response, id=response_id, requests__user__admin=request.user
            )

        if response_record.payment_status == "Paid":
            messages.info(request, "This service request has already been paid for.")
            return redirect("Viewappointment_history")

        if not response_record.total_amount or response_record.total_amount <= 0:
            response_record.calculate_bill(response_record.hours_worked or 1.0)
            response_record.save()

        context = {
            "response": response_record,
        }
        return render(request, "userpages/payment_checkout.html", context)

    def post(self, request, response_id):
        if request.user.is_superuser:
            response_record = get_object_or_404(Response, id=response_id)
        else:
            response_record = get_object_or_404(
                Response, id=response_id, requests__user__admin=request.user
            )

        if response_record.payment_status == "Paid":
            messages.info(request, "This bill has already been paid.")
            return redirect("Viewappointment_history")

        if not response_record.total_amount or response_record.total_amount <= 0:
            response_record.calculate_bill(response_record.hours_worked or 1.0)
            response_record.save()

        payment_method = request.POST.get("payment_method", "bKash").strip()
        account_number = request.POST.get("account_number", "").strip()

        prefix_map = {
            "bKash": "BKSH",
            "Nagad": "NGD",
            "Rocket": "RCKT",
            "Card": "CARD",
            "Cash on Delivery": "COD",
            "Cash": "COD",
        }
        prefix = prefix_map.get(payment_method, "PAY")
        txn_id = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

        response_record.payment_status = "Paid"
        response_record.payment_method = payment_method
        response_record.transaction_id = txn_id
        response_record.paid_at = timezone.now()
        response_record.status = True
        response_record.job_status = "Completed"
        response_record.save()

        # Automatically credit worker's virtual wallet balance with Decimal precision
        worker_instance = response_record.assigned_worker
        current_bal = Decimal(str(worker_instance.wallet_balance or "0.00"))
        earning = Decimal(str(response_record.worker_earning or "0.00"))
        worker_instance.wallet_balance = (current_bal + earning).quantize(Decimal("0.01"))
        worker_instance.save()

        # Send notifications
        send_notification(
            worker_instance.admin,
            "Payment Received!",
            f"Customer paid ৳{response_record.total_amount} for '{response_record.requests.service.Name}'. Your 90% share (৳{response_record.worker_earning}) has been added to your Wallet Balance.",
            link=reverse("worker_wallet"),
            notification_type="payment"
        )
        send_notification(
            request.user,
            "Payment Successful!",
            f"Payment of ৳{response_record.total_amount} completed via {payment_method}. TrxID: {txn_id}.",
            link=reverse("invoice_detail", args=[response_record.id]),
            notification_type="payment"
        )
        for admin_user in User.objects.filter(is_superuser=True):
            send_notification(
                admin_user,
                "Platform Commission Earned",
                f"Order #{response_record.id} paid. Platform commission (10% = ৳{response_record.admin_commission}) earned.",
                link=reverse("admin_payment_history"),
                notification_type="payment"
            )

        messages.success(
            request,
            f"Payment of ৳{response_record.total_amount} successfully completed via {payment_method}! "
            f"Transaction ID: {txn_id}. Platform fee (10% = ৳{response_record.admin_commission}) processed, "
            f"and ৳{response_record.worker_earning} (90%) credited to provider wallet."
        )
        return redirect("invoice_detail", response_id=response_record.id)


class reject(LoginRequiredMixin, WorkerRequiredMixin, View):
    def get(self, request, action, id):
        current_worker = get_object_or_404(workers, admin=request.user)
        response_record = Response.objects.filter(id=id, assigned_worker=current_worker).first()

        if not response_record:
            messages.error(request, "Task not found or not assigned to you.")
            return redirect("WorkerpendingTask")

        request_record = response_record.requests
        request_record.status = False
        request_record.save()
        response_record.delete()
        messages.info(request, f"Task '{request_record.service.Name}' rejected and returned to available requests.")

        return redirect("WorkerpendingTask")


# ==============================================================================
# Administrator Views
# ==============================================================================

class admmin_home(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        total_requests = ServiceRequests.objects.count()
        completed_requests = Response.objects.filter(status=True).count()
        assigned_requests_count = Response.objects.count()
        pending_requests = assigned_requests_count - completed_requests
        total_users = User.objects.filter(is_staff=False, is_superuser=False).count()
        latest_requests = ServiceRequests.objects.select_related("service", "user__admin").order_by("-dateofrequest")[:5]

        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        user_signups = (
            User.objects.filter(date_joined__gte=six_months_ago)
            .annotate(month=TruncMonth("date_joined"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        chart_labels = [signup["month"].strftime("%B") for signup in user_signups]
        chart_data = [signup["count"] for signup in user_signups]

        booking_counts = (
            ServiceRequests.objects.filter(dateofrequest__gte=six_months_ago)
            .annotate(month=TruncMonth("dateofrequest"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        bookings_chart_labels = [booking["month"].strftime("%B") for booking in booking_counts]
        bookings_chart_data = [booking["count"] for booking in booking_counts]

        total_platform_commission = Response.objects.filter(payment_status="Paid").aggregate(total=Sum("admin_commission"))["total"] or 0.00
        total_payment_volume = Response.objects.filter(payment_status="Paid").aggregate(total=Sum("total_amount"))["total"] or 0.00
        total_paid_orders = Response.objects.filter(payment_status="Paid").count()
        worker_payouts_total = Response.objects.filter(payment_status="Paid").aggregate(total=Sum("worker_earning"))["total"] or 0.00

        # 1. Platform Revenue Curve (Monthly GMV & 10% Fee)
        monthly_revenue = (
            Response.objects.filter(payment_status="Paid", paid_at__isnull=False)
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(
                gmv=Sum("total_amount"),
                commission=Sum("admin_commission")
            )
            .order_by("month")
        )
        if monthly_revenue.exists():
            revenue_labels = [r["month"].strftime("%b %Y") for r in monthly_revenue]
            revenue_gmv = [float(r["gmv"] or 0) for r in monthly_revenue]
            revenue_commission = [float(r["commission"] or 0) for r in monthly_revenue]
        else:
            revenue_labels = ["Current Month"]
            revenue_gmv = [float(total_payment_volume)]
            revenue_commission = [float(total_platform_commission)]

        # 2. City Demand Distribution (Doughnut / Pie Chart)
        city_demand = (
            ServiceRequests.objects.values("city__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:6]
        )
        city_labels = [c["city__name"] or "Other" for c in city_demand]
        city_counts = [c["total"] for c in city_demand]

        # 3. Top Earning Technicians Leaderboard
        top_workers = (
            Response.objects.filter(payment_status="Paid")
            .values(
                "assigned_worker__id",
                "assigned_worker__designation",
                "assigned_worker__admin__first_name",
                "assigned_worker__admin__last_name",
                "assigned_worker__admin__username",
                "assigned_worker__city",
            )
            .annotate(
                total_earned=Sum("worker_earning"),
                jobs_count=Count("id")
            )
            .order_by("-total_earned")[:5]
        )

        context = {
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "pending_requests": pending_requests,
            "total_users": total_users,
            "total_platform_commission": total_platform_commission,
            "total_payment_volume": total_payment_volume,
            "total_paid_orders": total_paid_orders,
            "worker_payouts_total": worker_payouts_total,
            "latest_requests": latest_requests,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data),
            "bookings_chart_labels": json.dumps(bookings_chart_labels),
            "bookings_chart_data": json.dumps(bookings_chart_data),
            "revenue_labels": json.dumps(revenue_labels),
            "revenue_gmv": json.dumps(revenue_gmv),
            "revenue_commission": json.dumps(revenue_commission),
            "city_labels": json.dumps(city_labels),
            "city_counts": json.dumps(city_counts),
            "top_workers": top_workers,
        }
        return render(request, "adminpages/adminhompage.html", context)


class manageworker(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        workers_records = workers.objects.select_related("admin").prefetch_related("service_areas").all().order_by("-created_at")
        context = {"workers_records": workers_records}
        return render(request, "adminpages/Manage_Workers.html", context)


class verify_worker(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, action, id):
        worker_to_verify = get_object_or_404(workers, id=id)
        if action == "active" and not worker_to_verify.acc_activation:
            worker_to_verify.acc_activation = True
            worker_to_verify.save()
            messages.success(
                request,
                f"Worker '{worker_to_verify.admin.get_full_name() or worker_to_verify.admin.username}' has been successfully verified.",
            )
        return redirect("manageworker")


class manageusers(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        users_records = users.objects.select_related("admin").all().order_by("-created_at")
        context = {"users_records": users_records}
        return render(request, "adminpages/View_Users.html", context)


class DeleteUserView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, user_id):
        if request.user.id == user_id:
            messages.error(request, "You cannot delete your own admin account.")
            return redirect("manageusers")

        user_to_delete = get_object_or_404(User, pk=user_id)
        name = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"Successfully deleted customer user: {name}")
        return redirect("manageusers")


class DeleteWorkerView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, worker_id):
        worker_to_delete = get_object_or_404(workers, pk=worker_id)
        user_account = worker_to_delete.admin
        name = user_account.username
        user_account.delete()
        messages.success(request, f"Successfully deleted service provider: {name}")
        return redirect("manageworker")


class ManageCountry(LoginRequiredMixin, SuperuserRequiredMixin, View):
    template_name = "adminpages/Manage_Country.html"

    def get(self, request):
        country_records = Country.objects.all().order_by("name")
        context = {
            "Country_record": country_records,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        country_name = request.POST.get("name", "").strip()
        if country_name:
            if Country.objects.filter(name__iexact=country_name).exists():
                messages.error(request, f"Country '{country_name}' already exists.")
            else:
                Country.objects.create(name=country_name)
                messages.success(request, f"Country '{country_name}' added successfully.")
        return redirect("ManageCountry")


class DeleteCountry(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, id):
        country = Country.objects.filter(id=id).first()
        if country:
            name = country.name
            country.delete()
            messages.success(request, f"Country '{name}' deleted successfully.")
        else:
            messages.error(request, "Country not found.")
        return redirect("ManageCountry")


class ManageState(LoginRequiredMixin, SuperuserRequiredMixin, View):
    template_name = "adminpages/ManageState.html"

    def get(self, request):
        form = stateform()
        states = State.objects.select_related("country").all().order_by("country__name", "name")
        context = {
            "form": form,
            "State_record": states,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = stateform(request.POST)
        if form.is_valid():
            state = form.save()
            messages.success(request, f"State '{state.name}' added successfully.")
            return redirect("ManageState")
        else:
            state_records = State.objects.select_related("country").all().order_by("country__name", "name")
            context = {
                "State_record": state_records,
                "form": form,
            }
            return render(request, self.template_name, context)


class DeleteState(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, id):
        state = State.objects.filter(id=id).first()
        if state:
            name = state.name
            state.delete()
            messages.success(request, f"State '{name}' deleted successfully.")
        else:
            messages.error(request, "State not found.")
        return redirect("ManageState")


class managecity(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        city_records = City.objects.all().order_by("name")
        states = State.objects.all().order_by("name")
        context = {
            "city_records": city_records,
            "state_recorsd": states,
        }
        return render(request, "adminpages/ManageCity.html", context)


class AddCity(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        states = State.objects.all().order_by("name")
        return render(request, "city.html", {"state_recorsd": states})

    def post(self, request):
        city_name = request.POST.get("name", "").strip()
        state_val = request.POST.get("state", "").strip()

        # If an ID is passed from a select option, resolve to state name
        if state_val.isdigit():
            state_obj = State.objects.filter(id=int(state_val)).first()
            if state_obj:
                state_val = state_obj.name

        if city_name and state_val:
            City.objects.create(name=city_name, state=state_val)
            messages.success(request, f"City '{city_name}' added successfully.")
        else:
            messages.error(request, "Both city name and state are required.")

        return redirect("managecity")


class DeleteCity(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, id):
        city = City.objects.filter(id=id).first()
        if city:
            name = city.name
            city.delete()
            messages.success(request, f"City '{name}' deleted successfully.")
        else:
            messages.error(request, "City not found.")
        return redirect("managecity")


class AddServices(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        return render(request, "adminpages/ServiceCatogry.html")

    def post(self, request):
        name = request.POST.get("Name", "").strip()
        description = request.POST.get("Description", "").strip()
        hourly_rate = request.POST.get("hourly_rate", "300.00").strip() or "300.00"
        img = request.FILES.get("img")

        if not name:
            messages.error(request, "Service name is required.")
            return render(request, "adminpages/ServiceCatogry.html")

        ServiceCatogarys.objects.create(
            Name=name,
            Description=description,
            img=img,
            hourly_rate=hourly_rate
        )
        messages.success(request, f"Service category '{name}' created successfully with rate ৳{hourly_rate}/hr.")
        return redirect("ManageServices")


class ManageServices(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        service_records = ServiceCatogarys.objects.all().order_by("Name")
        context = {
            "services": service_records,
        }
        return render(request, "adminpages/Manage_Services.html", context)


class EditServices(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, id):
        service = get_object_or_404(ServiceCatogarys, id=id)
        return render(request, "adminpages/ServiceCatogry.html", {"record": service})

    def post(self, request, id):
        service = get_object_or_404(ServiceCatogarys, id=id)
        name = request.POST.get("Name", "").strip()
        description = request.POST.get("Description", "").strip()
        hourly_rate = request.POST.get("hourly_rate", "").strip()
        img = request.FILES.get("img")

        if not name:
            messages.error(request, "Service name cannot be empty.")
            return render(request, "adminpages/ServiceCatogry.html", {"record": service})

        service.Name = name
        service.Description = description
        if hourly_rate:
            try:
                service.hourly_rate = float(hourly_rate)
            except ValueError:
                pass
        if img:
            service.img = img
        service.save()

        messages.success(request, f"Service category '{service.Name}' updated successfully (৳{service.hourly_rate}/hr).")
        return redirect("ManageServices")


class DeleteServices(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, id):
        service = ServiceCatogarys.objects.filter(id=id).first()
        if service:
            name = service.Name
            service.delete()
            messages.success(request, f"Service category '{name}' deleted successfully.")
        else:
            messages.error(request, "Service not found.")
        return redirect("ManageServices")


class AssignWorker(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, id):
        req = get_object_or_404(ServiceRequests, id=id)
        service = req.service.Name

        # Only verified workers who have the right designation and are available
        workers_records = workers.objects.filter(
            designation=service,
            avalability_status=True,
            acc_activation=True,
        ).prefetch_related("service_areas").select_related("admin")

        context = {
            "req": req,
            "workers_records": workers_records,
        }
        return render(request, "adminpages/assign_worker.html", context)

    def post(self, request, id):
        worker_id = request.POST.get("assigned_worker")
        req = get_object_or_404(ServiceRequests, id=id)

        if not worker_id:
            messages.error(request, "Please select an available provider.")
            return redirect("AssignWorker", id=id)

        try:
            assigned_worker = workers.objects.get(id=worker_id)
            req.status = True
            req.save()

            Response.objects.create(
                requests=req,
                assigned_worker=assigned_worker,
                status=False,
            )
            messages.success(
                request,
                f"Worker '{assigned_worker.admin.get_full_name() or assigned_worker.admin.username}' has been successfully assigned.",
            )
        except Exception as e:
            messages.error(request, f"Failed to assign worker: {e}")

        return redirect("viewresponse")


class ViewRequests(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        request_records = (
            ServiceRequests.objects.select_related("user__admin", "service", "city")
            .prefetch_related("selected_addons")
            .all()
            .order_by("-dateofrequest")
        )
        context = {
            "request_records": request_records,
        }
        return render(request, "adminpages/View_request.html", context)


class viewresponse(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        response_records = (
            Response.objects.select_related(
                "requests__service", "requests__user__admin", "requests__city", "assigned_worker__admin"
            )
            .prefetch_related("requests__selected_addons")
            .all()
            .order_by("-Date")
        )
        context = {
            "Response_records": response_records,
        }
        return render(request, "adminpages/view_response.html", context)


class viewfeedbacks(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request):
        feedback_records = (
            Feedback.objects.select_related("User", "Employ__admin")
            .all()
            .order_by("-Date")
        )

        stats = feedback_records.aggregate(
            average_rating=Avg("Rating"), total_reviews=Count("id")
        )

        context = {
            "feedback_records": feedback_records,
            "average_rating": stats["average_rating"] or 0,
            "total_reviews": stats["total_reviews"] or 0,
        }
        return render(request, "adminpages/View_feedbacks.html", context)


# ==============================================================================
# Payment History & Invoicing Views (Admin, Worker, Customer)
# ==============================================================================

class AdminPaymentHistoryView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """Allows administrators to inspect, search, filter, and export all platform transactions and 10% commission revenues."""
    def get(self, request):
        status_filter = request.GET.get("status", "").strip()
        method_filter = request.GET.get("method", "").strip()
        search_query = request.GET.get("q", "").strip()
        export_csv = request.GET.get("export", "").strip().lower() == "csv"

        payments = (
            Response.objects.select_related(
                "requests__service", "requests__user__admin", "requests__city", "assigned_worker__admin"
            )
            .prefetch_related("requests__selected_addons")
            .filter(Q(status=True) | Q(hours_worked__gt=0))
            .order_by("-paid_at", "-Date")
        )

        if status_filter in ["Paid", "Pending"]:
            payments = payments.filter(payment_status=status_filter)

        if method_filter:
            payments = payments.filter(payment_method__iexact=method_filter)

        if search_query:
            payments = payments.filter(
                Q(transaction_id__icontains=search_query)
                | Q(requests__user__admin__username__icontains=search_query)
                | Q(requests__user__admin__first_name__icontains=search_query)
                | Q(requests__user__admin__last_name__icontains=search_query)
                | Q(assigned_worker__admin__first_name__icontains=search_query)
                | Q(assigned_worker__admin__last_name__icontains=search_query)
                | Q(requests__service__Name__icontains=search_query)
            )

        if export_csv:
            response = HttpResponse(content_type="text/csv")
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            response["Content-Disposition"] = f'attachment; filename="servicehub_payments_{timestamp}.csv"'

            writer = csv.writer(response)
            writer.writerow([
                "Invoice ID", "Date", "Customer Name", "Customer Phone",
                "Worker Name", "Service Category", "Hours Worked", "Hourly Rate (BDT)",
                "Total Amount (BDT)", "Admin Commission 10% (BDT)", "Worker Share 90% (BDT)",
                "Payment Status", "Payment Method", "Transaction ID", "Paid At"
            ])

            for p in payments:
                writer.writerow([
                    f"INV-{p.id}{p.requests.id}",
                    p.Date.strftime("%Y-%m-%d %H:%M") if p.Date else "",
                    p.requests.user.admin.get_full_name() or p.requests.user.admin.username,
                    p.requests.user.contact_number,
                    p.assigned_worker.admin.get_full_name() or p.assigned_worker.admin.username,
                    p.requests.service.Name,
                    p.hours_worked,
                    p.hourly_rate,
                    p.total_amount,
                    p.admin_commission,
                    p.worker_earning,
                    p.payment_status,
                    p.payment_method or "N/A",
                    p.transaction_id or "N/A",
                    p.paid_at.strftime("%Y-%m-%d %H:%M:%S") if p.paid_at else "Unpaid"
                ])
            return response

        all_completed = Response.objects.filter(Q(status=True) | Q(hours_worked__gt=0))
        paid_records = all_completed.filter(payment_status="Paid")
        pending_records = all_completed.filter(payment_status="Pending")

        stats = {
            "total_commission": paid_records.aggregate(s=Sum("admin_commission"))["s"] or 0,
            "total_volume": paid_records.aggregate(s=Sum("total_amount"))["s"] or 0,
            "total_payouts": paid_records.aggregate(s=Sum("worker_earning"))["s"] or 0,
            "pending_volume": pending_records.aggregate(s=Sum("total_amount"))["s"] or 0,
            "paid_count": paid_records.count(),
            "pending_count": pending_records.count(),
        }

        context = {
            "payments": payments,
            "stats": stats,
            "current_status": status_filter,
            "current_method": method_filter,
            "search_query": search_query,
        }
        return render(request, "adminpages/payment_history.html", context)


class WorkerPaymentHistoryView(LoginRequiredMixin, View):
    """Allows workers to view their earned payouts, logged hours, commission deductions, and pending payments."""
    def get(self, request):
        if not request.user.is_staff and not workers.objects.filter(admin=request.user).exists():
            messages.error(request, "Access restricted to Service Providers.")
            return redirect("index")

        worker = get_object_or_404(workers, admin=request.user)
        status_filter = request.GET.get("status", "").strip()
        search_query = request.GET.get("q", "").strip()

        payments = (
            Response.objects.select_related(
                "requests__service", "requests__user__admin", "requests__city"
            )
            .prefetch_related("requests__selected_addons")
            .filter(assigned_worker=worker, status=True)
            .order_by("-paid_at", "-Date")
        )

        if status_filter in ["Paid", "Pending"]:
            payments = payments.filter(payment_status=status_filter)

        if search_query:
            payments = payments.filter(
                Q(transaction_id__icontains=search_query)
                | Q(requests__user__admin__first_name__icontains=search_query)
                | Q(requests__user__admin__last_name__icontains=search_query)
                | Q(requests__service__Name__icontains=search_query)
            )

        all_worker_jobs = Response.objects.filter(assigned_worker=worker, status=True)
        paid_jobs = all_worker_jobs.filter(payment_status="Paid")
        pending_jobs = all_worker_jobs.filter(payment_status="Pending")

        stats = {
            "total_net_earnings": paid_jobs.aggregate(s=Sum("worker_earning"))["s"] or 0,
            "pending_earnings": pending_jobs.aggregate(s=Sum("worker_earning"))["s"] or 0,
            "total_jobs": all_worker_jobs.count(),
            "total_hours": all_worker_jobs.aggregate(h=Sum("hours_worked"))["h"] or 0,
            "paid_jobs_count": paid_jobs.count(),
        }

        context = {
            "payments": payments,
            "stats": stats,
            "worker": worker,
            "current_status": status_filter,
            "search_query": search_query,
        }
        return render(request, "workerpages/payment_history.html", context)


class CustomerPaymentHistoryView(LoginRequiredMixin, View):
    """Allows customers to view invoices, settlement history, payment receipts, and pending bills."""
    def get(self, request):
        status_filter = request.GET.get("status", "").strip()
        search_query = request.GET.get("q", "").strip()

        payments = (
            Response.objects.select_related(
                "requests__service", "assigned_worker__admin", "requests__city"
            )
            .prefetch_related("requests__selected_addons")
            .filter(requests__user__admin=request.user, status=True)
            .order_by("-paid_at", "-Date")
        )

        if status_filter in ["Paid", "Pending"]:
            payments = payments.filter(payment_status=status_filter)

        if search_query:
            payments = payments.filter(
                Q(transaction_id__icontains=search_query)
                | Q(requests__service__Name__icontains=search_query)
                | Q(assigned_worker__admin__first_name__icontains=search_query)
                | Q(assigned_worker__admin__last_name__icontains=search_query)
            )

        all_cust_jobs = Response.objects.filter(requests__user__admin=request.user, status=True)
        paid_jobs = all_cust_jobs.filter(payment_status="Paid")
        pending_jobs = all_cust_jobs.filter(payment_status="Pending")

        stats = {
            "total_spent": paid_jobs.aggregate(s=Sum("total_amount"))["s"] or 0,
            "total_due": pending_jobs.aggregate(s=Sum("total_amount"))["s"] or 0,
            "total_orders": all_cust_jobs.count(),
            "paid_orders_count": paid_jobs.count(),
            "pending_orders_count": pending_jobs.count(),
        }

        context = {
            "payments": payments,
            "stats": stats,
            "current_status": status_filter,
            "search_query": search_query,
        }
        return render(request, "userpages/customer_payment_history.html", context)


class InvoiceDetailView(LoginRequiredMixin, View):
    """Provides a professional, printable invoice page accessible to Admin, Customer, and the assigned Worker."""
    def get(self, request, response_id):
        response_obj = get_object_or_404(
            Response.objects.select_related(
                "requests__service", "requests__user__admin", "requests__city", "assigned_worker__admin"
            ),
            id=response_id,
        )

        is_owner = (response_obj.requests.user.admin == request.user)
        is_worker = (response_obj.assigned_worker.admin == request.user)
        is_admin = request.user.is_superuser

        if not (is_owner or is_worker or is_admin):
            messages.error(request, "You do not have permission to view this invoice.")
            return redirect("index")

        if is_worker:
            base_template = "workerpages/worker_header_footer.html"
        elif is_admin:
            base_template = "adminpages/admin_header_footer.html"
        else:
            base_template = "userpages/user_header_footer.html"

        context = {
            "base_template": base_template,
            "response": response_obj,
            "is_owner": is_owner,
            "is_worker": is_worker,
            "is_admin": is_admin,
        }
        return render(request, "userpages/invoice_detail.html", context)


# ==============================================================================
# In-App Live Chat System
# ==============================================================================

class JobChatView(LoginRequiredMixin, View):
    """Interactive chat room between customer and worker for an active/assigned service request."""
    def get(self, request, response_id):
        response_obj = get_object_or_404(
            Response.objects.select_related("requests__user__admin", "assigned_worker__admin", "requests__service"),
            id=response_id
        )

        is_customer = (response_obj.requests.user.admin == request.user)
        is_worker = (response_obj.assigned_worker.admin == request.user)
        is_admin = request.user.is_superuser

        if not (is_customer or is_worker or is_admin):
            messages.error(request, "You do not have permission to access this chat.")
            return redirect("index")

        # Mark incoming messages as read
        ChatMessage.objects.filter(response=response_obj).exclude(sender=request.user).update(is_read=True)

        messages_list = ChatMessage.objects.filter(response=response_obj).select_related("sender").order_by("timestamp")
        partner = response_obj.assigned_worker.admin if is_customer else response_obj.requests.user.admin
        partner_phone = response_obj.assigned_worker.contact_number if is_customer else response_obj.requests.contact

        if is_worker:
            base_template = "workerpages/worker_header_footer.html"
        elif is_admin:
            base_template = "adminpages/admin_header_footer.html"
        else:
            base_template = "userpages/user_header_footer.html"

        context = {
            "base_template": base_template,
            "response": response_obj,
            "chat_messages": messages_list,
            "partner": partner,
            "partner_phone": partner_phone,
            "is_customer": is_customer,
            "is_worker": is_worker,
        }
        return render(request, "chat/job_chat.html", context)


class GetChatMessagesView(LoginRequiredMixin, View):
    """AJAX endpoint for polling new chat messages in real time."""
    def get(self, request, response_id):
        response_obj = get_object_or_404(Response, id=response_id)
        is_customer = (response_obj.requests.user.admin == request.user)
        is_worker = (response_obj.assigned_worker.admin == request.user)
        is_admin = request.user.is_superuser

        if not (is_customer or is_worker or is_admin):
            return JsonResponse({"error": "Unauthorized"}, status=403)

        ChatMessage.objects.filter(response=response_obj).exclude(sender=request.user).update(is_read=True)

        messages_list = ChatMessage.objects.filter(response=response_obj).select_related("sender").order_by("timestamp")
        data = []
        for m in messages_list:
            data.append({
                "id": m.id,
                "sender_name": m.sender.get_full_name() or m.sender.username,
                "is_me": (m.sender == request.user),
                "message": m.message,
                "time": m.timestamp.strftime("%I:%M %p"),
                "date": m.timestamp.strftime("%b %d"),
            })
        return JsonResponse({"messages": data})


class SendChatMessageView(LoginRequiredMixin, View):
    """AJAX endpoint to send a new chat message."""
    def post(self, request, response_id):
        response_obj = get_object_or_404(
            Response.objects.select_related("requests__user__admin", "assigned_worker__admin"),
            id=response_id
        )
        is_customer = (response_obj.requests.user.admin == request.user)
        is_worker = (response_obj.assigned_worker.admin == request.user)
        is_admin = request.user.is_superuser

        if not (is_customer or is_worker or is_admin):
            return JsonResponse({"error": "Unauthorized"}, status=403)

        text = request.POST.get("message", "").strip()
        if not text:
            return JsonResponse({"error": "Empty message"}, status=400)

        msg = ChatMessage.objects.create(
            response=response_obj,
            sender=request.user,
            message=text,
        )

        # Notify recipient
        recipient = response_obj.assigned_worker.admin if is_customer else response_obj.requests.user.admin
        send_notification(
            recipient,
            f"New message from {request.user.get_full_name() or request.user.username}",
            f"{text[:60]}",
            link=reverse("job_chat", args=[response_obj.id]),
            notification_type="chat"
        )

        return JsonResponse({
            "success": True,
            "message": {
                "id": msg.id,
                "sender_name": request.user.get_full_name() or request.user.username,
                "is_me": True,
                "message": msg.message,
                "time": msg.timestamp.strftime("%I:%M %p"),
                "date": msg.timestamp.strftime("%b %d"),
            }
        })


# ==============================================================================
# Worker Wallet & Withdrawal Views
# ==============================================================================

class WorkerWalletView(LoginRequiredMixin, WorkerRequiredMixin, View):
    """Allows worker to view current wallet balance, earning statistics, and withdrawal history."""
    def get(self, request):
        worker = get_object_or_404(workers, admin=request.user)
        withdrawals = WithdrawalRequest.objects.filter(worker=worker).order_by("-created_at")

        total_earned = Response.objects.filter(assigned_worker=worker, payment_status="Paid").aggregate(s=Sum("worker_earning"))["s"] or Decimal("0.00")
        total_withdrawn = withdrawals.filter(status="Approved").aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        pending_withdraw = withdrawals.filter(status="Pending").aggregate(s=Sum("amount"))["s"] or Decimal("0.00")

        context = {
            "worker": worker,
            "withdrawals": withdrawals,
            "total_earned": total_earned,
            "total_withdrawn": total_withdrawn,
            "pending_withdraw": pending_withdraw,
        }
        return render(request, "workerpages/worker_wallet.html", context)


class RequestWithdrawalView(LoginRequiredMixin, WorkerRequiredMixin, View):
    """Handles worker withdrawal requests with escrow hold on balance."""
    def post(self, request):
        worker = get_object_or_404(workers, admin=request.user)
        amount_raw = request.POST.get("amount", "0").strip()
        method = request.POST.get("payment_method", "bKash").strip()
        account_number = request.POST.get("account_number", "").strip()
        bank_name = request.POST.get("bank_name", "").strip()
        notes = request.POST.get("notes", "").strip()

        # Normalize method
        if method == "Bank":
            method = "Bank Transfer"
        elif method not in ["bKash", "Nagad", "Rocket", "Bank Transfer"]:
            method = "bKash"

        try:
            amount = Decimal(str(amount_raw)).quantize(Decimal("0.01"))
        except (ValueError, TypeError, InvalidOperation):
            amount = Decimal("0.00")

        if amount < Decimal("100.00"):
            messages.error(request, "Minimum withdrawal amount is ৳100.00.")
            return redirect("worker_wallet")

        if not account_number:
            messages.error(request, "Account number is required for payout.")
            return redirect("worker_wallet")

        # Validate account number format
        if method in ["bKash", "Nagad", "Rocket"]:
            clean_acct = re.sub(r'[\s\-+]', '', account_number)
            if clean_acct.startswith("880"):
                clean_acct = clean_acct[2:]
            if not (clean_acct.isdigit() and len(clean_acct) == 11 and clean_acct.startswith("01")):
                messages.error(request, f"Invalid {method} account number '{account_number}'. Must be a valid 11-digit Bangladeshi mobile number starting with 01 (e.g. 01700000000).")
                return redirect("worker_wallet")
            account_number = clean_acct
        elif method == "Bank Transfer":
            if not bank_name:
                messages.error(request, "Bank Name and Branch details are required for Bank Transfer.")
                return redirect("worker_wallet")
            if len(account_number) < 5:
                messages.error(request, "Please enter a valid Bank Account Number.")
                return redirect("worker_wallet")

        with transaction.atomic():
            # Acquire lock to prevent double-spending or race condition
            locked_worker = workers.objects.select_for_update().get(id=worker.id)
            available_balance = Decimal(str(locked_worker.wallet_balance or "0.00"))

            if amount > available_balance:
                messages.error(request, f"Insufficient balance. Your current available wallet balance is ৳{available_balance}.")
                return redirect("worker_wallet")

            # Deduct immediately from available wallet balance (hold in escrow)
            locked_worker.wallet_balance = (available_balance - amount).quantize(Decimal("0.01"))
            locked_worker.save()

            # Create withdrawal request
            withdrawal = WithdrawalRequest.objects.create(
                worker=locked_worker,
                amount=amount,
                payment_method=method,
                account_number=account_number,
                bank_name=bank_name,
                notes=notes,
                status="Pending"
            )

        # Notify admins
        for superuser in User.objects.filter(is_superuser=True):
            send_notification(
                superuser,
                "New Withdrawal Request",
                f"Worker {worker.admin.get_full_name() or worker.admin.username} requested payout of ৳{amount} via {method} ({account_number}).",
                link=reverse("manage_withdrawals"),
                notification_type="wallet"
            )

        messages.success(request, f"Withdrawal request #WDR-{withdrawal.id} of ৳{amount} submitted! ৳{amount} held from balance and will be disbursed shortly by admin.")
        return redirect("worker_wallet")


class ManageWithdrawalsView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """Allows Admin to inspect, search, and process worker withdrawal requests."""
    def get(self, request):
        status_filter = request.GET.get("status", "").strip()
        withdrawals = WithdrawalRequest.objects.select_related("worker__admin").order_by("-created_at")

        if status_filter in ["Pending", "Approved", "Rejected"]:
            withdrawals = withdrawals.filter(status=status_filter)

        stats = {
            "pending_count": WithdrawalRequest.objects.filter(status="Pending").count(),
            "pending_amount": WithdrawalRequest.objects.filter(status="Pending").aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "approved_amount": WithdrawalRequest.objects.filter(status="Approved").aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "total_requests": WithdrawalRequest.objects.count(),
        }

        context = {
            "withdrawals": withdrawals,
            "stats": stats,
            "current_status": status_filter,
        }
        return render(request, "adminpages/manage_withdrawals.html", context)


class ReviewWithdrawalView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """Admin approves or rejects a worker's withdrawal request."""
    def get(self, request, id, action):
        return redirect("manage_withdrawals")

    def post(self, request, id, action):
        withdrawal = get_object_or_404(WithdrawalRequest.objects.select_related("worker__admin"), id=id)
        admin_notes = request.POST.get("admin_notes", "").strip()
        transaction_id = request.POST.get("transaction_id", "").strip()

        if withdrawal.status != "Pending":
            messages.warning(request, f"This withdrawal request #WDR-{withdrawal.id} has already been processed (Current status: {withdrawal.status}).")
            return redirect("manage_withdrawals")

        if action == "approve":
            with transaction.atomic():
                locked_req = WithdrawalRequest.objects.select_for_update().get(id=id)
                if locked_req.status != "Pending":
                    messages.info(request, "This request was already processed.")
                    return redirect("manage_withdrawals")

                trx = transaction_id or f"TXN-{uuid.uuid4().hex[:8].upper()}"
                locked_req.status = "Approved"
                locked_req.admin_notes = admin_notes
                locked_req.transaction_id = trx
                locked_req.reviewed_at = timezone.now()
                locked_req.save()

            messages.success(request, f"Withdrawal #WDR-{withdrawal.id} of ৳{withdrawal.amount} approved for {withdrawal.worker.admin.get_full_name()}! TrxID: {trx}")
            send_notification(
                withdrawal.worker.admin,
                "Withdrawal Approved!",
                f"Your withdrawal request of ৳{withdrawal.amount} ({withdrawal.payment_method}) has been approved! TrxID: {trx}.",
                link=reverse("worker_wallet"),
                notification_type="wallet"
            )

        elif action == "reject":
            with transaction.atomic():
                locked_req = WithdrawalRequest.objects.select_for_update().get(id=id)
                if locked_req.status != "Pending":
                    messages.info(request, "This request was already processed.")
                    return redirect("manage_withdrawals")

                # Refund the held amount back to the worker's wallet balance
                worker_to_refund = workers.objects.select_for_update().get(id=locked_req.worker_id)
                current_bal = Decimal(str(worker_to_refund.wallet_balance or "0.00"))
                refund_amt = Decimal(str(locked_req.amount or "0.00"))
                worker_to_refund.wallet_balance = (current_bal + refund_amt).quantize(Decimal("0.01"))
                worker_to_refund.save()

                locked_req.status = "Rejected"
                locked_req.admin_notes = admin_notes
                locked_req.reviewed_at = timezone.now()
                locked_req.save()

            messages.warning(request, f"Withdrawal request #WDR-{withdrawal.id} rejected. ৳{withdrawal.amount} has been safely refunded to {withdrawal.worker.admin.get_full_name()}'s wallet balance.")
            send_notification(
                withdrawal.worker.admin,
                "Withdrawal Rejected - Funds Refunded",
                f"Your payout request of ৳{withdrawal.amount} was rejected and refunded to your wallet. Note: {admin_notes or 'Not specified'}.",
                link=reverse("worker_wallet"),
                notification_type="wallet"
            )

        return redirect("manage_withdrawals")


# ==============================================================================
# Notification Views
# ==============================================================================

class MarkNotificationReadView(LoginRequiredMixin, View):
    def get(self, request, id):
        notif = get_object_or_404(Notification, id=id, user=request.user)
        notif.is_read = True
        notif.save()
        if notif.link:
            return redirect(notif.link)
        return redirect("index")


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        referer = request.META.get("HTTP_REFERER") or "/"
        return HttpResponseRedirect(referer)

    def get(self, request):
        return self.post(request)


