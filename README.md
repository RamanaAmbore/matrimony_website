# Matrimony Website

This is a Django-based Matrimony website designed with a simple and intuitive interface for users to register, enter their profile details, search for prospective matches, and make payments for premium features. It includes Google authentication, WhatsApp OTP for mobile registration, and Razorpay integration for payments.

## Features

- **User Authentication**:
  - Google (Gmail) authentication.
  - WhatsApp OTP for mobile registration.
  
- **Profile Management**:
  - Users can add and update their profile details.
  - Upload profile pictures and blurred images.
  - Add and update the Nakshatram (Vedic astrology sign).

- **Search & Matching**:
  - Search for prospective matches with blurred images by default.
  - Full-size images available to approved users.
  
- **Admin Dashboard**:
  - Admins can manage user registrations.
  - Admins can approve other admins (requires site owner approval).
  
- **Payment Integration**:
  - Razorpay integration for payments.
  - Users can make payments for premium features.

## Prerequisites

- Python 3.8+
- Django 4.2+
- Razorpay API Key (Sign up at [Razorpay](https://razorpay.com/))
- WhatsApp OTP integration (for user phone verification)

## Installation

### Step 1: Clone the repository
```bash
git clone <repository_url>
cd matrimony_project
