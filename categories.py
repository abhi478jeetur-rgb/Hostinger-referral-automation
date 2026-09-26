"""
100 Easiest & High-Converting Business Categories for Hosting Services
Sourced directly from the Master Strategy Document.
"""

TOP_20_EASIEST_NICHES = [
    "Web Development Agencies",
    "Digital Marketing & SEO Agencies",
    "E-commerce Stores",
    "Freelance Web Designers",
    "Real Estate Agencies & Brokers",
    "Bloggers & Affiliate Marketers",
    "SaaS (Software as a Service) Startups",
    "Photographers & Videographers",
    "Restaurants, Cafes & Cloud Kitchens",
    "Healthcare Clinics & Dentists",
    "Law Firms & Attorneys",
    "Educational Institutes & Online Tutors",
    "Travel Agencies & Tour Operators",
    "Fitness Centers & Gyms",
    "Event & Wedding Planners",
    "IT Support & Consulting Firms",
    "Accounting & Financial Advisors",
    "Interior Designers & Architects",
    "Salons, Spas & Beauty Parlors",
    "Plumbers, Electricians & HVAC (Local Services)"
]

ALL_100_CATEGORIES = {
    "🏆 Top 20 High Priority": TOP_20_EASIEST_NICHES,
    "Tech, Digital & Creative": [
        "Web Development Agencies",
        "Digital Marketing & SEO Agencies",
        "Freelance Web Designers",
        "SaaS Startups",
        "Bloggers & Affiliate Marketers",
        "IT Support & Consulting Firms",
        "Graphic Design Studios",
        "Video Production Companies",
        "App Development Companies",
        "Podcasters & Broadcasters",
        "Virtual Assistant Businesses",
        "PR & Communication Agencies"
    ],
    "E-commerce & Retail": [
        "E-commerce Stores",
        "Jewelry Stores",
        "Fashion Boutiques",
        "Furniture Stores",
        "Hardware Stores",
        "Florists & Plant Shops",
        "Gift Shops",
        "Bookstores",
        "Toy & Hobby Shops",
        "Sporting Goods Stores",
        "Music Instrument Stores",
        "Antique Dealers",
        "Party Supply Stores"
    ],
    "Professional & Corporate Services": [
        "Law Firms & Attorneys",
        "Accounting & Financial Advisors",
        "HR & Recruitment Agencies",
        "Translation Services",
        "Insurance Agencies",
        "Tax Preparation Services",
        "Stockbrokers & Investment Firms",
        "Security Agencies",
        "Private Investigators",
        "Co-working Spaces"
    ],
    "Real Estate, Construction & Local Services": [
        "Real Estate Agencies & Brokers",
        "Interior Designers & Architects",
        "Plumbers & Pipefitters",
        "Electricians",
        "Roofing Contractors",
        "Painting Contractors",
        "Cleaning Services",
        "Landscaping & Lawn Care",
        "Pest Control Services",
        "Moving & Packing Companies",
        "Locksmiths",
        "Waste Management Services",
        "Solar Energy Companies"
    ],
    "Healthcare, Wellness & Beauty": [
        "Healthcare Clinics & Dentists",
        "Salons, Spas & Beauty Parlors",
        "Fitness Centers & Gyms",
        "Yoga Studios",
        "Massage Therapists",
        "Chiropractors",
        "Optometrists",
        "Pharmacies",
        "Medical Laboratories",
        "Personal Trainers",
        "Tattoo & Piercing Parlors"
    ],
    "Food, Hospitality & Travel": [
        "Restaurants & Cafes",
        "Travel Agencies & Tour Operators",
        "Bakeries",
        "Food Trucks",
        "Catering Services",
        "Breweries & Wineries",
        "Bed and Breakfasts",
        "Boutique Hotels",
        "Hostels"
    ],
    "Education & Childcare": [
        "Educational Institutes & Schools",
        "Online Course Creators & Tutors",
        "Daycare Centers",
        "Language Schools",
        "Driving Schools",
        "Martial Arts Studios",
        "Dance Studios"
    ],
    "Events & Entertainment": [
        "Photographers & Videographers",
        "Event & Wedding Planners",
        "Recording Studios",
        "Musicians & Bands",
        "DJs & Entertainment Services",
        "Art Galleries",
        "Museums"
    ],
    "Automotive": [
        "Automobile Repair Shops",
        "Car Dealerships",
        "Car Wash & Detailing Services",
        "Towing Services"
    ],
    "Pets & Animals": [
        "Pet Grooming Services",
        "Veterinary Clinics",
        "Animal Shelters & Rescues",
        "Pet Training Services"
    ],
    "Logistics & Manufacturing": [
        "Logistics & Freight Companies",
        "Courier Services",
        "Warehousing Services",
        "Import/Export Businesses",
        "Manufacturing Companies",
        "Wholesale Distributors",
        "Agriculture & Farming Businesses"
    ],
    "Miscellaneous": [
        "Dry Cleaners & Laundromats",
        "Tailors & Alteration Services",
        "Non-Profit Organizations & Charities"
    ]
}

def get_flattened_categories():
    """Return all unique categories in a clean flat list."""
    seen = set()
    result = []
    # Add top 20 first
    for cat in TOP_20_EASIEST_NICHES:
        if cat not in seen:
            seen.add(cat)
            result.append(cat)
    # Add remainder
    for group, cats in ALL_100_CATEGORIES.items():
        for cat in cats:
            if cat not in seen:
                seen.add(cat)
                result.append(cat)
    return result
