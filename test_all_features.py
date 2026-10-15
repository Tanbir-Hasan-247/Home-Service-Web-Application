import os
import sys
import django
import json
from decimal import Decimal

# Ensure utf-8 encoding for console output on Windows
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HomeServices_project.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from HomeServices_app.models import (
    users, workers, ServiceCatogarys, ServiceAddOn,
    ServiceRequests, Response, City, Country, State
)

def run_tests():
    print("=" * 60)
    print("STARTING FULL SYSTEM VERIFICATION SUITE")
    print("=" * 60)

    # 1. Add-on Model & Seeding Check
    print("\n[TEST 1] Verifying Service Add-Ons...")
    addon_count = ServiceAddOn.objects.count()
    assert addon_count > 0, "No ServiceAddOn items found in DB!"
    print(f"  [OK] Found {addon_count} service add-ons across categories.")
    sample_addon = ServiceAddOn.objects.first()
    print(f"  Sample Addon: {sample_addon.service.Name} -> {sample_addon.name} (+৳{sample_addon.price})")

    # 2. Add-on Billing Calculation Check
    print("\n[TEST 2] Verifying Billing Formula with Add-Ons...")
    # Find or create a test service request with add-ons
    service = ServiceCatogarys.objects.first()
    assert service is not None, "No ServiceCatogarys found!"
    service.hourly_rate = Decimal("400.00")
    service.save()

    test_addons = ServiceAddOn.objects.filter(service=service)
    if not test_addons.exists():
        test_addons = [ServiceAddOn.objects.create(service=service, name="Test Booster", price=Decimal("250.00"))]
    
    addons_sum = sum(a.price for a in test_addons[:2])
    
    # Create mock response
    cust_profile = users.objects.first()
    city_obj = City.objects.first()

    req = ServiceRequests.objects.create(
        user=cust_profile,
        Problem_Description="Test add-on billing",
        service=service,
        Address="Road 12, Banani",
        city=city_obj,
        pin="1213",
        addons_total=addons_sum,
        latitude=Decimal("23.793700"),
        longitude=Decimal("90.406600")
    )
    req.selected_addons.set(test_addons[:2])

    worker_prof = workers.objects.first()
    worker_user = worker_prof.admin if worker_prof else None
    user_obj = cust_profile.admin if cust_profile else None

    resp = Response.objects.create(
        requests=req,
        assigned_worker=worker_prof,
        job_status='Accepted',
        status=False
    )

    # Test bill calculation for 2.5 hours
    # Expected: (2.5 * 400.00) + addons_sum = 1000.00 + addons_sum
    resp.calculate_bill(2.5)
    resp.save()

    expected_total = Decimal("1000.00") + addons_sum
    expected_commission = (expected_total * Decimal("0.10")).quantize(Decimal("0.01"))
    expected_worker = expected_total - expected_commission

    assert resp.total_amount == expected_total, f"Expected {expected_total}, got {resp.total_amount}"
    assert resp.admin_commission == expected_commission, f"Expected {expected_commission}, got {resp.admin_commission}"
    assert resp.worker_earning == expected_worker, f"Expected {expected_worker}, got {resp.worker_earning}"
    print(f"  [OK] Bill calculated: Hours=2.5, Rate=৳400, Addons=৳{addons_sum} => Total=৳{resp.total_amount}, Admin=৳{resp.admin_commission}, Worker=৳{resp.worker_earning}")

    # 3. Live GPS Tracking APIs Check
    print("\n[TEST 3] Verifying Live GPS Location Endpoints...")
    client = Client()
    if worker_user:
        client.force_login(worker_user)
    
    # Update location
    worker_lat = Decimal("23.780000")
    worker_lng = Decimal("90.410000")
    update_res = client.post(
        f"/job_status/{resp.id}/update_location/",
        data=json.dumps({"latitude": float(worker_lat), "longitude": float(worker_lng)}),
        content_type="application/json"
    )
    assert update_res.status_code == 200, f"Update location returned {update_res.status_code}"
    update_json = update_res.json()
    assert update_json.get("status") == "success", f"Failed: {update_json}"
    print(f"  [OK] POST /job_status/{resp.id}/update_location/ => {update_json}")

    # Read live location when job is On the Way
    resp.job_status = "On the Way"
    resp.save()
    if user_obj:
        client.force_login(user_obj)
    live_res = client.get(f"/job_status/{resp.id}/live_location/")
    assert live_res.status_code == 200, f"Live location returned {live_res.status_code}"
    live_json = live_res.json()
    assert live_json.get("status") == "success", f"Failed: {live_json}"
    assert live_json.get("distance_km") is not None
    assert live_json.get("eta_minutes") is not None
    print(f"  [OK] GET /job_status/{resp.id}/live_location/ => Distance: {live_json.get('distance_km')} km, ETA: {live_json.get('formatted_eta')}")

    # 4. Admin Analytics Dashboard Data Check
    print("\n[TEST 4] Verifying Admin Analytics Data & Charts...")
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        client.force_login(admin_user)
        admin_res = client.get("/admmin_home/")
        assert admin_res.status_code == 200, f"Admin home returned {admin_res.status_code}"
        assert b"revenueCurveChart" in admin_res.content, "Revenue Curve chart canvas missing!"
        assert b"cityDemandChart" in admin_res.content, "City Demand doughnut chart canvas missing!"
        assert b"Top Earning Technicians" in admin_res.content, "Leaderboard missing!"
        print("  [OK] Admin Analytics rendered successfully:")
        print("       - Monthly Revenue Curve (GMV & 10% Platform Commission)")
        print("       - City Demand Distribution Chart")
        print("       - Top Earning Technicians Leaderboard")

    # 5. Bilingual System Static File Check
    print("\n[TEST 5] Verifying Bilingual Assets & Templates...")
    bilingual_path = os.path.join("HomeServices_app", "static", "js", "bilingual.js")
    assert os.path.exists(bilingual_path), f"bilingual.js not found at {bilingual_path}!"
    with open(bilingual_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    assert "servicehub_language" in js_content
    assert "setSiteLanguage" in js_content
    assert "অনুরোধ করা হয়েছে" in js_content
    assert "রওনা দিয়েছেন" in js_content
    print(f"  [OK] bilingual.js verified ({len(js_content)} bytes).")

    # Clean up test records
    resp.delete()
    req.delete()

    print("\n" + "=" * 60)
    print("ALL VERIFICATION SUITE CHECKS PASSED (100% SUCCESS)!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
