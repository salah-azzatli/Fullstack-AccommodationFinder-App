# ─────────────Prompt────────────────────────────────────────────────

    ```
    # Frontend-Backend Integration Review

    You are a senior Frontend Developer.

    Your task is to review the frontend project and connect it with the backend.

    ## Objectives

    1. Analyze the frontend codebase.

    2. Analyze the backend API endpoints provided.

    3. Verify that every frontend API call matches the backend endpoint.

    4. Detect any integration issues such as:

    * Wrong URL paths
    * Missing endpoints
    * Incorrect HTTP methods
    * Incorrect request payloads
    * Incorrect response handling
    * Authentication conflicts
    * JWT token handling issues
    * Pagination mismatches
    * Naming inconsistencies
    * Missing environment variables
    * CORS-related assumptions
    * File upload mismatches
    * WebSocket mismatches

    5. Connect the frontend to the backend using the provided Base URL.

    ## Debug Report

    If any issue is found, create a file:

    frontend/debug.md

    The file should contain:

    ### Issue

    Description of the problem.

    ### Location

    File path and line number if possible.

    ### Cause

    Why the issue occurs.

    ### Fix

    Exact code change required.

    ### Status

    * Critical
    * Warning
    * Info

    ## Integration Rules

    * Do not change backend endpoints.
    * Update frontend code whenever possible.
    * Use the provided Base URL.
    * Reuse existing frontend architecture and patterns.
    * Verify authentication flow using JWT access and refresh tokens.

    ## Deliverables

    1. Connected frontend application.
    2. Updated API service files.
    3. frontend/debug.md containing all detected issues.
    4. Summary of:

    * Connected endpoints
    * Failed integrations
    * Required backend changes (if any)

    ## Backend Base URL

    /api/

    ## API Groups

    * /api/token/
    * /api/token/refresh/
    * /api/auth/
    * /api/properties/
    * /api/bookings/
    * /api/favorites/
    * /api/reviews/
    * /api/roommates/
    * /api/community/
    * /api/messaging/
    * /api/notifications/
    * /api/payments/
    * /api/services/

    ## Important

    Do not assume endpoint details.

    Inspect the backend folder and use the actual urlpatterns, serializers, views, and API responses to determine the correct integration.


    ```
# ─────────────Prompt──────────────────────────────────────────────────


# ─────────────Start App API EndPoints────────────────────────────────────────────────

    ```
    
    ```
# ─────────────End App API EndPoints──────────────────────────────────────────────────



# ─────────────Start Apps APIs────────────────────────────────────────────────
    ```
    from django.urls import include, path
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

    urlpatterns = [
        # JWT auth endpoints for obtaining and refreshing tokens
        path('token/'        , TokenObtainPairView.as_view() , name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view() ,    name='token_refresh'),
        
        path('auth/'         , include('api.accounts_api.urls')),
        path('properties/'   , include('api.properties_api.urls')),
        path('bookings/'     , include('api.bookings_api.urls')),
        path('favorites/'    , include('api.favorites_api.urls')),
        path('reviews/'      , include('api.reviews_api.urls')),
        path('roommates/'    , include('api.roommates_api.urls')),
        path('community/'    , include('api.community_api.urls')),
        path('messaging/'    , include('api.messaging_api.urls')),
        path('notifications/', include('api.notifications_api.urls')),
        path('payments/'     , include('api.payments_api.urls')),
        path('services/'     , include('api.services_api.urls')),
    ]
    ```
# ─────────────End Apps APIs────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────

    ```
    from django.contrib import admin
    from django.conf import settings
    from django.conf.urls.static import static
    from django.urls import include, path

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/', include('api.urls')),
    ]

    ```
# ─────────────────────────────────────────────────────────────
