import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Product, Review
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate realistic Indian reviews for products'

    def handle(self, *args, **options):
        # Indian names for reviewers
        indian_names = [
            # Male names
            'Rajesh Kumar', 'Amit Sharma', 'Rohit Singh', 'Vikash Gupta', 'Suresh Patel',
            'Manoj Yadav', 'Deepak Verma', 'Sandeep Kumar', 'Ajay Joshi', 'Ravi Agarwal',
            'Ashok Mishra', 'Pradeep Tiwari', 'Nitin Sinha', 'Rakesh Pandey', 'Sanjay Dubey',
            'Vinod Chandra', 'Mukesh Jain', 'Ramesh Rao', 'Praveen Nair', 'Harish Reddy',
            'Kiran Mehta', 'Ankit Saxena', 'Yogesh Bansal', 'Manish Goyal', 'Sachin Mittal',
            'Gaurav Khanna', 'Vivek Arora', 'Naveen Kapoor', 'Shubham Agrawal', 'Abhishek Shukla',
            
            # Female names
            'Priya Sharma', 'Pooja Singh', 'Neha Gupta', 'Ritu Patel', 'Sunita Yadav',
            'Kavita Verma', 'Meera Kumar', 'Asha Joshi', 'Geeta Agarwal', 'Suman Mishra',
            'Rekha Tiwari', 'Nisha Sinha', 'Usha Pandey', 'Radha Dubey', 'Shanti Chandra',
            'Kamala Jain', 'Lakshmi Rao', 'Sarita Nair', 'Vandana Reddy', 'Anita Mehta',
            'Preeti Saxena', 'Swati Bansal', 'Divya Goyal', 'Kiran Mittal', 'Seema Khanna',
            'Anjali Arora', 'Rachna Kapoor', 'Shikha Agrawal', 'Sneha Shukla', 'Jyoti Soni'
        ]

        # Review templates - Mix of Hindi, English, and Hinglish
        review_templates = {
            'positive_4_star': [
                # Pure Hindi reviews
                "Bahut achha lighter hai bhai! {product_specific} Design ekdam mast hai aur working bhi proper hai. Delivery bhi time pe ayi thi. Bas ek choti si problem hai {minor_issue} but overall satisfied hun. Recommend karunga!",
                
                "Accha purchase kiya! {product_specific} Look and feel premium lagta hai. Bas {minor_issue} but overall happy hun. Friends ko bhi recommend karunga desi quality hai yeh!",
                
                "Lighter bahut sundar hai! {product_specific} Weight perfect hai - na jyada heavy na light. {minor_issue} warna 5 star deta. Chalega yeh! paisa vasool product",
                
                # Pure English reviews
                "Great quality lighter! {product_specific} The build feels premium and the flame is consistent. Only issue is {minor_issue} but still worth buying. Good product overall.",
                
                "Nice product received on time. {product_specific} Works perfectly fine. Just one small issue - {minor_issue}. Otherwise happy with the purchase. Will recommend to others.",
                
                "Solid construction and good finish. {product_specific} The lighter works as expected. Minor complaint about {minor_issue} but that's acceptable for this price range.",
                
                # Hinglish mix
                "Very good product yaar! {product_specific} Quality achhi hai, lekin {minor_issue}. Price ke hisaab se theek hai. Ghar pe sab logo ko pasand aya. Thanks smokeking!",
                
                "Good lighter for the price! {product_specific} Design unique hai aur flame bhi consistent hai. {minor_issue} isliye ek star kam. But happy overall with delivery and packaging!",
                
                "Nice lighter received! {product_specific} Vintage look bohot accha hai. Working fine hai bas {minor_issue}. Value for money product hai definitely.",
                
                "Solid build quality! {product_specific} Feel premium hai haath mein. Bas {minor_issue} warna perfect product tha. Recommended for sure!"
            ],
            
            'positive_5_star': [
                # Pure Hindi reviews
                "Ekdam perfect lighter! {product_specific} Bilkul waise hi mila jaisa photo mein dikhaya tha. Quality top-notch hai aur flame bhi smooth hai. Full 5 star product! Highly recommended bhai!",
                
                "Fantastic lighter bhai! {product_specific} Design mind-blowing hai aur functionality bhi perfect. Money worth product hai completely. Highly satisfied! Dil khush kar diya!",
                
                "Zabardast lighter mila hai! {product_specific} Bilkul perfect working hai. Flame bhi steady milti hai. Smokeking ki quality hamesha top class hoti hai. 5 star!",
                
                # Pure English reviews  
                "Excellent quality lighter! {product_specific} The craftsmanship is outstanding. Flame ignition is smooth and consistent. Highly satisfied with this purchase. 5 stars!",
                
                "Perfect product! {product_specific} Amazing build quality and the design is exactly as shown. Works flawlessly. Best lighter I've bought so far. Highly recommended!",
                
                "Outstanding lighter received! {product_specific} Premium materials used and excellent finish. The flame is perfect and refilling is easy. Worth every penny!",
                
                # Hinglish mix
                "Outstanding product! {product_specific} Build quality extraordinary hai. Flame consistent aur refillable feature bhi mast hai. Smokeking se hamesha achha experience milta hai. Perfect 5/5!",
                
                "Superb lighter received! {product_specific} Premium feel hai bilkul. Working excellent hai aur look bhi bohot attractive hai. Must buy product hai yeh! Thanks smokeking team!",
                
                "Brilliant product bhai! {product_specific} Vintage design with modern functionality. Working flawless hai. Best purchase ever! Thanks for such amazing product quality!",
                
                "Top class lighter! {product_specific} Weight perfect hai aur grip comfortable hai. Flame stable aur refilling easy hai. Full marks to smokeking! Will buy more items."
            ]
        }

        # Product-specific phrases - Mix of Hindi, English, and Hinglish
        product_phrases = {
            'nunchaku': [
                "Nunchaku style bohot cool lagta hai",
                "The nunchaku design is totally unique", 
                "Brass nunchaku finish amazing hai",
                "Rotating nunchaku mechanism works smoothly",
                "Nunchaku concept is really innovative",
                "Love the nunchaku style - so different!"
            ],
            'vintage': [
                "Vintage look bilkul royal lagta hai",
                "The retro design is absolutely classic",
                "Vintage finish gives premium feel", 
                "Old school style - love it completely",
                "Antique look absolutely gorgeous hai",
                "Retro vibe is just perfect for me"
            ],
            'brass': [
                "Brass material solid feel deta hai",
                "The brass finish is shiny and durable",
                "Golden brass color looks attractive",
                "Brass weight feels just right in hand",
                "Pure brass quality excellent hai",
                "Solid brass construction - very sturdy"
            ],
            'wheel': [
                "Wheel mechanism smooth chalti hai",
                "The rotating wheel is easy to use",
                "Wheel grip comfortable hai completely",
                "Wheel ignition system works reliably",
                "360 rotation feature mast hai",
                "The wheel action is so satisfying"
            ],
            'kerosene': [
                "Kerosene refillable option convenient hai",
                "Kerosene capacity is quite sufficient",
                "Kerosene flame burns very steady",
                "Traditional kerosene lighter feel hai",
                "Refillable kerosene tank practical hai",
                "Love the authentic kerosene flame"
            ],
            'cigar': [
                "Cigar cutter works perfectly smooth",
                "Sharp blade cuts cigars cleanly",
                "Cigar cutting mechanism excellent hai",
                "Perfect for cigar enthusiasts like me",
                "Clean cut every time - amazing!",
                "Stainless steel blade bohot sharp hai"
            ]
        }

        # Minor issues for 4-star reviews - Mix of Hindi and English
        minor_issues = [
            "thoda sa tight hai wheel",
            "delivery took 1-2 extra days",
            "instruction manual hindi mein nahi tha",
            "packaging could have been better",
            "flame adjustment takes some time",
            "cap thoda loose fit hai",
            "minor scratches on the polish",
            "kerosene smell thoda strong hai initially",
            "weight is slightly more than expected",
            "chain clasp is a bit tight",
            "the color was slightly different from photo",
            "arrived without proper bubble wrap"
        ]

        self.stdout.write('Starting review generation...')

        # Create dummy users if they don't exist
        created_users = []
        for i, name in enumerate(indian_names):
            first_name = name.split()[0]
            last_name = ' '.join(name.split()[1:])
            username = f"reviewer_{i+1}"
            email = f"reviewer{i+1}@example.com"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': f"9{random.randint(100000000, 999999999)}"
                }
            )
            created_users.append(user)

        self.stdout.write(f'Created/retrieved {len(created_users)} users')

        # Generate reviews for each product
        products = Product.objects.all()
        total_reviews = 0

        for product in products:
            # Generate 100-150 reviews per product
            num_reviews = random.randint(100, 150)
            
            # Determine product characteristics
            product_name_lower = product.name.lower()
            product_specific_phrases = []
            
            if 'nunchaku' in product_name_lower:
                product_specific_phrases.extend(product_phrases['nunchaku'])
            if 'vintage' in product_name_lower or 'retro' in product_name_lower:
                product_specific_phrases.extend(product_phrases['vintage'])
            if 'brass' in product_name_lower:
                product_specific_phrases.extend(product_phrases['brass'])
            if 'wheel' in product_name_lower:
                product_specific_phrases.extend(product_phrases['wheel'])
            if 'kerosene' in product_name_lower:
                product_specific_phrases.extend(product_phrases['kerosene'])
            if 'cigar' in product_name_lower or 'cutter' in product_name_lower:
                product_specific_phrases.extend(product_phrases['cigar'])
            
            # Fallback phrases
            if not product_specific_phrases:
                product_specific_phrases = [
                    "Product quality bahut achhi hai",
                    "Design bilkul mast hai",
                    "Build quality solid hai",
                    "Look and feel premium hai",
                    "Working perfect hai"
                ]

            # Generate reviews
            for _ in range(num_reviews):
                # 70% chance for 5 stars, 30% for 4 stars
                rating = 5 if random.random() < 0.7 else 4
                
                # Select random user
                user = random.choice(created_users)
                
                # Skip if user already reviewed this product
                if Review.objects.filter(product=product, user=user).exists():
                    continue
                
                # Select review template
                if rating == 5:
                    review_text = random.choice(review_templates['positive_5_star'])
                else:
                    review_text = random.choice(review_templates['positive_4_star'])
                
                # Fill in product-specific phrase
                product_phrase = random.choice(product_specific_phrases)
                
                # For 4-star reviews, add minor issue
                if rating == 4:
                    minor_issue = random.choice(minor_issues)
                    review_text = review_text.format(
                        product_specific=product_phrase,
                        minor_issue=minor_issue
                    )
                else:
                    review_text = review_text.format(product_specific=product_phrase)
                
                # Generate title (optional)
                title_options = [
                    "",  # 40% chance of no title
                    "Excellent Product!",
                    "Good Quality",
                    "Worth Buying",
                    "Satisfied",
                    "Nice Lighter",
                    "Recommended",
                    "Value for Money",
                    "Happy Purchase",
                    "Top Quality"
                ]
                title = random.choice(title_options) if random.random() > 0.4 else ""
                
                # Random date between Jan 2025 to Aug 2025
                start_date = datetime.date(2025, 1, 1)
                end_date = datetime.date(2025, 8, 31)
                time_between = end_date - start_date
                days_between = time_between.days
                random_days = random.randrange(days_between)
                random_date = start_date + datetime.timedelta(days=random_days)
                
                # Convert to datetime and make timezone aware
                random_hour = random.randint(9, 21)  # Between 9 AM and 9 PM
                random_minute = random.randint(0, 59)
                created_datetime = datetime.datetime.combine(random_date, datetime.time(random_hour, random_minute))
                created_date = timezone.make_aware(created_datetime)
                
                # Create review (created_at will be auto-set)
                review = Review.objects.create(
                    product=product,
                    user=user,
                    rating=rating,
                    title=title,
                    review=review_text,
                    is_verified_purchase=random.choice([True, False]),  # Random verification
                    is_approved=True  # Pre-approve demo reviews
                )
                
                # Update the created_at field manually to override auto_now_add
                Review.objects.filter(id=review.id).update(created_at=created_date)
                
                total_reviews += 1

            self.stdout.write(f'Generated {num_reviews} reviews for: {product.name[:50]}...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {total_reviews} reviews for {products.count()} products!')
        )