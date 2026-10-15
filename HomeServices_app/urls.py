from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from HomeServices_app import views
from HomeServices_project import settings
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView,
    PasswordResetCompleteView
)

urlpatterns = [

    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logout', views.logout_view),
    path('signup/', views.signup_selection_view, name='signup_selection'),
    path('user_registration/', views.User_Register.as_view(), name='user_registration'),
    path('Worker_Register/', views.Worker_Register.as_view(), name='Worker_Register'),
    path('', views.home.as_view(), name='index'),
    path('about/', views.about.as_view(), name='about'),
    path('services/', views.services.as_view(), name='services'),
    path('contact/', views.contact.as_view(), name='contact'),
    path('bookservice/<int:id>', views.bookservice.as_view(), name='bookservice'),

    path('admmin_home/', views.admmin_home.as_view(), name='admmin_home'),
    path('admin_home/', views.admmin_home.as_view(), name='admin_home'),
    path('workers_home/', views.workers_home.as_view(), name='workers_home'),

    path('manageworker/', views.manageworker.as_view(), name='manageworker'),
    path('manageusers/', views.manageusers.as_view(), name='manageusers'),
    path('verify_worker/<str:action>/<int:id>',views.verify_worker.as_view(),name='verify_worker'),

    path('ManageCountry/', views.ManageCountry.as_view(), name='ManageCountry'),
    path('DeleteCountry/<int:id>',views.DeleteCountry.as_view(),name='DeleteCountry'),

    path('AddCity/', views.AddCity.as_view(), name='AddCity'),
    path('managecity/', views.managecity.as_view(), name='managecity'),
    path('DeleteCity/<int:id>',views.DeleteCity.as_view(),name='DeleteCity'),

    path('ManageState/', views.ManageState.as_view(), name='ManageState'),
    path('DeleteState/<int:id>',views.DeleteState.as_view(),name='DeleteState'),


    path('AddServices/', views.AddServices.as_view(), name='AddServices'),
    path('ManageServices/', views.ManageServices.as_view(), name='ManageServices'),
    path('DeleteServices/<int:id>',views.DeleteServices.as_view(),name='DeleteServices'),
    path('EditServices/<int:id>',views.EditServices.as_view(),name='EditServices'),
    path('admin-users/delete/<int:user_id>/', views.DeleteUserView.as_view(), name='delete_user'),
    path('admin-workers/delete/<int:worker_id>/', views.DeleteWorkerView.as_view(), name='delete_worker'),

    path('AssignWorker/<int:id>',views.AssignWorker.as_view(),name='AssignWorker'),
   

    path('feedback_form/', views.feedback_form.as_view(), name='feedback_form'),
    path('feedback/<int:worker_id>/', views.feedback_form.as_view(), name='feedback_form_for_worker'),
    path('viewfeedbacks/', views.viewfeedbacks.as_view(), name='viewfeedbacks'),
    path('ViewRequests/', views.ViewRequests.as_view(), name='ViewRequests'),
    path('viewresponse/',views.viewresponse.as_view(),name='viewresponse'),

    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    path('profile/delete/', views.DeleteProfileView.as_view(), name='delete_profile'),
    path('Viewappointment_history/',views.Viewappointment_history.as_view(),name='Viewappointment_history'),
    path('payment/<int:response_id>/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('invoice/<int:response_id>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('admin-payments/', views.AdminPaymentHistoryView.as_view(), name='admin_payment_history'),
    path('worker-payments/', views.WorkerPaymentHistoryView.as_view(), name='worker_payment_history'),
    path('user-payments/', views.CustomerPaymentHistoryView.as_view(), name='customer_payment_history'),
    path('CancelRequest/<int:id>',views.CancelRequest.as_view(),name='CancelRequest'),
    path('userprofile/',views.userprofile.as_view(),name='userprofile'),
    path('workerprofile/',views.workerprofile.as_view(),name='workerprofile'),
   


    path('worker/profile/edit/', views.EditWorkerProfileView.as_view(), name='edit_worker_profile'),
    path('worker/profile/delete/', views.DeleteWorkerProfileView.as_view(), name='delete_worker_profile'),
    path('worker/availability/toggle/', views.ToggleAvailabilityView.as_view(), name='toggle_availability'),
    path('colleague/<int:pk>/', views.ColleagueProfileView.as_view(), name='colleague_profile'),
    path('ViewColleagues/', views.ViewColleagues.as_view(), name='ViewColleagues'),
    path('WorkerViewRequests/', views.WorkerViewRequests.as_view(), name='WorkerViewRequests'),
    path('viewworkerfeedbacks/', views.viewworkerfeedbacks.as_view(), name='viewworkerfeedbacks'),
    path('WorkerpendingTask/',views.workerviewresponse.as_view(),name='WorkerpendingTask'),

    path('acceptrequest/<str:action>/<int:id>',views.acceptrequest.as_view(),name='acceptrequest'),
    path('markcompleted/<str:action>/<int:id>',views.markcompleted.as_view(),name='markcompleted'),
    path('reject/<str:action>/<int:id>',views.reject.as_view(),name='reject'),
    

    path('job_status/<int:id>/update_location/', views.UpdateWorkerLocationView.as_view(), name='update_worker_location'),
    path('job_status/<int:id>/live_location/', views.GetLiveLocationView.as_view(), name='get_live_location'),
    path('job_status/<int:id>/<str:new_status>/', views.UpdateJobStatusView.as_view(), name='update_job_status'),

    # In-App Live Chat
    path('chat/<int:response_id>/', views.JobChatView.as_view(), name='job_chat'),
    path('chat/<int:response_id>/messages/', views.GetChatMessagesView.as_view(), name='get_chat_messages'),
    path('chat/<int:response_id>/send/', views.SendChatMessageView.as_view(), name='send_chat_message'),

    # Worker Wallet & Payout Withdrawals
    path('worker/wallet/', views.WorkerWalletView.as_view(), name='worker_wallet'),
    path('worker/withdraw/', views.RequestWithdrawalView.as_view(), name='request_withdrawal'),
    path('admin-withdrawals/', views.ManageWithdrawalsView.as_view(), name='manage_withdrawals'),
    path('admin-withdrawals/<int:id>/<str:action>/', views.ReviewWithdrawalView.as_view(), name='review_withdrawal'),

    # Notifications
    path('notifications/read/<int:id>/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/read-all/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),

    # Password Reset
    path('password-reset/',PasswordResetView.as_view(template_name='password_reset.html',html_email_template_name='password_reset_email.html'),name='password-reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),
]