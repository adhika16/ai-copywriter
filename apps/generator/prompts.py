"""
Prompt templates for Indonesian Creative Economy AI Copywriter
Optimized for Indonesian language and cultural context
"""

from typing import Dict, List, Optional
from django.utils.html import escape


class PromptTemplates:
    """Collection of prompt templates for different content types"""
    
    # Tone variations in Indonesian
    TONES = {
        'professional': 'profesional dan terpercaya',
        'casual': 'santai dan ramah',
        'luxury': 'mewah dan eksklusif',
        'friendly': 'akrab dan hangat',
        'energetic': 'energik dan bersemangat',
        'minimalist': 'sederhana dan elegan',
        'traditional': 'tradisional dan berbudaya',
        'modern': 'modern dan inovatif'
    }
    
    # Length specifications
    LENGTHS = {
        'short': {
            'description': 'singkat (50-100 kata)',
            'caption': 'pendek (20-50 kata)',
            'headline': 'ringkas (5-15 kata)'
        },
        'medium': {
            'description': 'sedang (100-200 kata)',
            'caption': 'sedang (50-100 kata)',
            'headline': 'sedang (10-20 kata)'
        },
        'long': {
            'description': 'panjang (200-400 kata)',
            'caption': 'panjang (100-150 kata)',
            'headline': 'detail (15-30 kata)'
        }
    }
    
    @staticmethod
    def product_description(product_info: Dict, length: str = "medium", tone: str = "professional") -> str:
        """Generate product description prompt"""
        tone_desc = PromptTemplates.TONES.get(tone, 'profesional dan terpercaya')
        length_desc = PromptTemplates.LENGTHS[length]['description']
        
        # Extract product information safely
        name = escape(product_info.get('name', ''))
        category = escape(product_info.get('category', ''))
        price = product_info.get('price', '')
        features = product_info.get('features', '')
        target_audience = product_info.get('target_audience', '')
        brand_story = product_info.get('brand_story', '')
        
        return f"""
Kamu adalah copywriter ahli untuk produk ekonomi kreatif Indonesia. Buatkan deskripsi produk yang menarik dan persuasif dengan detail berikut:

INFORMASI PRODUK:
- Nama Produk: {name}
- Kategori: {category}
- Harga: {price}
- Fitur/Keunggulan: {features}
- Target Audience: {target_audience}
- Cerita Brand: {brand_story}

REQUIREMENTS:
- Tone: {tone_desc}
- Panjang: {length_desc}
- Bahasa: Indonesia yang natural dan menarik
- Fokus pada nilai unik produk Indonesia
- Sertakan emotional appeal yang kuat
- Gunakan storytelling yang relatable untuk orang Indonesia
- Hindari klise yang berlebihan
- Akhiri dengan call-to-action yang menarik

STRUKTUR YANG DIINGINKAN:
1. Hook pembuka yang menarik perhatian
2. Deskripsi produk dan keunggulan utama
3. Benefit untuk pembeli
4. Social proof atau credibility (jika relevan)
5. Call-to-action yang persuasif

Pastikan konten mendukung ekonomi kreatif lokal dan menunjukkan kebanggaan terhadap produk Indonesia.
"""

    @staticmethod
    def social_media_caption(product_info: Dict, platform: str = "instagram", length: str = "medium") -> str:
        """Generate social media caption prompt"""
        length_desc = PromptTemplates.LENGTHS[length]['caption']
        
        name = escape(product_info.get('name', ''))
        category = escape(product_info.get('category', ''))
        description = product_info.get('description', '')
        price = product_info.get('price', '')
        
        platform_specs = {
            'instagram': {
                'style': 'visual dan engaging dengan emoji',
                'hashtags': '10-15 hashtag yang relevan',
                'limit': '2200 karakter',
                'features': 'cerita di balik produk, behind-the-scenes'
            },
            'facebook': {
                'style': 'storytelling yang lebih panjang',
                'hashtags': '3-5 hashtag utama',
                'limit': 'flexible, fokus pada engagement',
                'features': 'community building, sharing value'
            },
            'tiktok': {
                'style': 'catchy dan trending',
                'hashtags': '5-8 hashtag viral',
                'limit': '2200 karakter',
                'features': 'hook kuat di awal, call-to-action jelas'
            },
            'twitter': {
                'style': 'ringkas dan impactful',
                'hashtags': '2-3 hashtag fokus',
                'limit': '280 karakter',
                'features': 'pesan singkat tapi berkesan'
            }
        }
        
        spec = platform_specs.get(platform, platform_specs['instagram'])
        
        return f"""
Buatkan caption media sosial yang engaging untuk platform {platform.upper()} dengan detail produk:

INFORMASI PRODUK:
- Nama Produk: {name}
- Kategori: {category}
- Deskripsi: {description}
- Harga: {price}

PLATFORM REQUIREMENTS ({platform.upper()}):
- Style: {spec['style']}
- Panjang: {length_desc}
- Hashtag: {spec['hashtags']}
- Batas karakter: {spec['limit']}
- Fitur khusus: {spec['features']}

GUIDELINES:
- Gunakan bahasa Indonesia yang natural dan gaul (sesuai target audience)
- Mulai dengan hook yang menarik perhatian
- Ceritakan value proposition dengan jelas
- Sertakan emotional connection
- Gunakan emoji yang relevan (terutama untuk Instagram/TikTok)
- Tambahkan call-to-action yang mendorong engagement
- Dukung produk lokal Indonesia
- Hashtag harus campuran antara trending dan niche

FORMAT OUTPUT:
[Caption utama]

[Hashtag dalam baris terpisah]

Pastikan caption mendorong interaksi dan mendukung ekonomi kreatif Indonesia!
"""

    @staticmethod
    def marketing_headline(product_info: Dict, 
                         headline_type: str = "attention_grabbing", 
                         usage_context: str = "website",
                         character_limit: Optional[int] = None,
                         tone: str = "profesional",
                         variations: int = 5,
                         additional_instructions: str = "") -> str:
        """Generate marketing headline prompt with advanced options"""
        
        name = escape(product_info.get('name', ''))
        category = escape(product_info.get('category', ''))
        key_benefits = product_info.get('key_benefits', '')
        unique_selling_point = product_info.get('unique_selling_point', '')
        target_audience = product_info.get('target_audience', '')
        problem_solved = product_info.get('problem_solved', '')
        price_range = product_info.get('price_range', '')
        
        headline_types = {
            'attention_grabbing': 'Headlines yang langsung menarik perhatian dengan hook yang kuat',
            'benefit_focused': 'Headlines yang fokus pada manfaat utama produk',
            'curiosity_driven': 'Headlines yang membangkitkan rasa penasaran dan ingin tahu lebih',
            'problem_solving': 'Headlines yang menekankan solusi masalah yang dipecahkan',
            'urgency_scarcity': 'Headlines yang menciptakan rasa urgensi dan kelangkaan',
            'social_proof': 'Headlines yang menggunakan testimoni, review, atau validasi sosial',
            'local_pride': 'Headlines yang menekankan kebanggaan produk lokal Indonesia',
            'emotional_appeal': 'Headlines yang menyentuh emosi dan perasaan audience'
        }
        
        usage_contexts = {
            'website': 'Website/Landing Page - harus SEO friendly dan convert visitor menjadi customer',
            'social_media_ads': 'Iklan Media Sosial - harus scroll-stopping dan engaging di feed',
            'email_marketing': 'Email Subject Line - harus membuat recipient ingin buka email',
            'google_ads': 'Google Ads - harus relevan dengan search intent dan click-worthy',
            'banner_display': 'Banner/Display Ads - harus visible dan impactful secara visual',
            'print_media': 'Media Cetak - harus powerful tanpa interaksi digital',
            'video_thumbnail': 'Video Thumbnail - harus curiosity-driven untuk click',
            'product_packaging': 'Kemasan Produk - harus menarik di retail shelf',
            'press_release': 'Press Release - harus newsworthy dan media-friendly'
        }
        
        tones = {
            'profesional': 'profesional dan kredibel',
            'kasual': 'santai dan friendly',
            'energik': 'energik dan enthusiastic',
            'mewah': 'eksklusif dan premium',
            'ramah': 'ramah dan hangat',
            'inspiratif': 'inspiratif dan motivational',
            'playful': 'playful dan fun',
            'edukatif': 'informatif dan edukatif'
        }
        
        focus = headline_types.get(headline_type, headline_types['attention_grabbing'])
        context_desc = usage_contexts.get(usage_context, usage_contexts['website'])
        tone_desc = tones.get(tone, tones['profesional'])
        
        character_limit_text = f"\n- Batasan karakter: MAKSIMAL {character_limit} karakter" if character_limit else ""
        additional_text = f"\n\nINSTRUKSI TAMBAHAN:\n{additional_instructions}" if additional_instructions else ""
        
        # Generate dynamic output format based on variations
        output_format = "\n".join([f"{i}. [Headline {i}]" for i in range(1, variations + 1)])
        
        return f"""
Buatkan {variations} headline marketing yang powerful untuk produk ekonomi kreatif Indonesia:

INFORMASI PRODUK:
- Nama Produk: {name}
- Kategori: {category}
- Manfaat Utama: {key_benefits}
- Unique Selling Point: {unique_selling_point}
- Target Audience: {target_audience}
- Masalah yang Dipecahkan: {problem_solved}
- Rentang Harga: {price_range}

REQUIREMENTS:
- Tipe headline: {headline_type}
  ({focus})
- Konteks penggunaan: {usage_context}
  ({context_desc})
- Tone: {tone_desc}
- Bahasa: Indonesia yang impactful{character_limit_text}

GUIDELINES:
- Setiap headline harus unik dan powerful
- Gunakan power words yang kuat dalam bahasa Indonesia
- Ciptakan emotional hook atau logical appeal yang sesuai
- Relevan dengan budaya dan nilai-nilai Indonesia
- Mudah diingat dan share-worthy
- Sesuaikan dengan karakteristik platform/media yang digunakan
- Fokus pada benefit, bukan hanya fitur
- Gunakan angka atau statistik jika relevan
- Pastikan setiap headline berbeda satu sama lain

FORMAT OUTPUT:
Berikan {variations} headline yang berbeda, masing-masing dalam baris terpisah:
{output_format}{additional_text}

Buat headline yang benar-benar akan membuat target audience ingin tahu lebih tentang produk ini!
"""

    @staticmethod
    def email_marketing(product_info: Dict, email_type: str = "promotional", tone: str = "friendly") -> str:
        """Generate email marketing content prompt"""
        tone_desc = PromptTemplates.TONES.get(tone, 'akrab dan hangat')
        
        name = escape(product_info.get('name', ''))
        category = escape(product_info.get('category', ''))
        price = product_info.get('price', '')
        features = product_info.get('features', '')
        
        email_types = {
            'promotional': 'email promosi dengan penawaran khusus',
            'welcome': 'email selamat datang untuk customer baru',
            'follow_up': 'email follow-up setelah pembelian',
            'newsletter': 'newsletter dengan konten edukatif',
            'announcement': 'email pengumuman produk baru'
        }
        
        purpose = email_types.get(email_type, 'email promosi dengan penawaran khusus')
        
        return f"""
Buatkan konten email marketing untuk produk ekonomi kreatif Indonesia:

INFORMASI PRODUK:
- Nama Produk: {name}
- Kategori: {category}
- Harga: {price}
- Fitur/Keunggulan: {features}

EMAIL REQUIREMENTS:
- Tipe: {email_type} ({purpose})
- Tone: {tone_desc}
- Target: Customer Indonesia yang tertarik produk lokal
- Goal: Mendorong engagement dan mendukung ekonomi kreatif

STRUKTUR EMAIL:
1. Subject line yang menarik (buat 3 variasi)
2. Opening yang personal dan hangat
3. Body content yang engaging
4. Clear call-to-action
5. Closing yang memorable

GUIDELINES:
- Gunakan personalisasi yang natural
- Sertakan social proof jika relevan
- Bangun emotional connection dengan produk lokal
- Gunakan storytelling yang relatable
- Include urgency atau scarcity jika sesuai
- Pastikan mobile-friendly dalam penulisan
- Dukung mission ekonomi kreatif Indonesia

Buatkan email yang tidak hanya menjual, tapi juga membangun relationship!
"""

    @staticmethod
    def website_copy(product_info: Dict, section: str = "hero", tone: str = "professional") -> str:
        """Generate website copy prompt"""
        tone_desc = PromptTemplates.TONES.get(tone, 'profesional dan terpercaya')
        
        name = escape(product_info.get('name', ''))
        category = escape(product_info.get('category', ''))
        value_proposition = product_info.get('value_proposition', '')
        benefits = product_info.get('benefits', '')
        
        sections = {
            'hero': 'hero section dengan headline utama dan value proposition',
            'about': 'about section yang menceritakan brand story',
            'features': 'features section yang menjelaskan keunggulan produk',
            'testimonial': 'testimonial section dengan social proof',
            'cta': 'call-to-action section yang persuasif'
        }
        
        section_desc = sections.get(section, 'hero section dengan headline utama')
        
        return f"""
Buatkan copy website untuk {section_desc} produk ekonomi kreatif Indonesia:

INFORMASI PRODUK:
- Nama Produk: {name}
- Kategori: {category}
- Value Proposition: {value_proposition}
- Benefits: {benefits}

REQUIREMENTS:
- Section: {section.upper()}
- Tone: {tone_desc}
- Audience: Visitor website yang tertarik produk lokal berkualitas
- Goal: Meningkatkan konversi dan membangun trust

GUIDELINES UNTUK {section.upper()}:
{"- Headline yang powerful dan benefit-driven" if section == 'hero' else ""}
{"- Subheadline yang menjelaskan value proposition" if section == 'hero' else ""}
{"- Ceritakan journey dan passion di balik brand" if section == 'about' else ""}
{"- Fokus pada transformasi yang ditawarkan" if section == 'about' else ""}
{"- List keunggulan dengan benefit-oriented language" if section == 'features' else ""}
{"- Gunakan bullet points yang scannable" if section == 'features' else ""}
{"- Include social proof yang credible" if section == 'testimonial' else ""}
{"- Showcase hasil nyata dari customer" if section == 'testimonial' else ""}
{"- Action-oriented language yang persuasif" if section == 'cta' else ""}
{"- Clear next step untuk visitor" if section == 'cta' else ""}

TONE & STYLE:
- Gunakan bahasa Indonesia yang professional tapi approachable
- Sertakan emotional appeal yang kuat
- Bangun credibility dan trust
- Dukung ekonomi kreatif lokal
- Fokus pada customer benefit, bukan hanya fitur
- Gunakan social proof dan local insights

Buatkan copy yang tidak hanya informatif, tapi juga persuasif dan membangun emotional connection!
"""

    @staticmethod
    def content_series(product_info: Dict, series_type: str = "educational", post_count: int = 5) -> str:
        """Generate content series prompt"""
        name = escape(product_info.get('name', ''))
        category = escape(product_info.get('category', ''))
        expertise_area = product_info.get('expertise_area', '')
        
        series_types = {
            'educational': 'konten edukatif yang memberikan value',
            'behind_scenes': 'behind-the-scenes process pembuatan',
            'user_generated': 'panduan untuk user-generated content',
            'seasonal': 'konten yang disesuaikan dengan musim/event',
            'tutorial': 'tutorial penggunaan atau tips'
        }
        
        series_desc = series_types.get(series_type, 'konten edukatif')
        
        return f"""
Buatkan rencana konten series untuk mendukung produk ekonomi kreatif Indonesia:

INFORMASI PRODUK:
- Nama Produk: {name}
- Kategori: {category}
- Area Expertise: {expertise_area}

SERIES REQUIREMENTS:
- Tipe: {series_type} ({series_desc})
- Jumlah konten: {post_count} post
- Platform: Multi-platform (IG, FB, TikTok)
- Goal: Brand awareness & community building

GUIDELINES:
- Setiap post harus standalone tapi saling connected
- Berikan value nyata kepada audience
- Incorporate storytelling Indonesia
- Include call-to-action yang natural
- Dukung ekonomi kreatif lokal
- Engagement-driven content
- Educational value yang tinggi

FORMAT OUTPUT:
Untuk setiap post dalam series, berikan:

POST [Nomor]:
Judul: [Judul menarik]
Hook: [Opening yang grab attention]
Konten utama: [Isi konten yang valuable]
Visual suggestion: [Saran visual/foto]
Hashtag strategy: [5-10 hashtag relevan]
CTA: [Call-to-action yang sesuai]

Pastikan setiap post membangun trust dan mendorong organic engagement!
"""


class PromptValidator:
    """Validate and sanitize prompt inputs"""
    
    @staticmethod
    def clean_product_info(product_info: Dict) -> Dict:
        """Clean and validate product information"""
        cleaned = {}
        
        # Required fields
        required_fields = ['name', 'category']
        for field in required_fields:
            if field not in product_info or not product_info[field]:
                raise ValueError(f"Field '{field}' is required")
            cleaned[field] = escape(str(product_info[field]).strip())
        
        # Optional fields
        optional_fields = [
            'price', 'features', 'target_audience', 'brand_story',
            'unique_selling_point', 'value_proposition', 'benefits',
            'description', 'expertise_area'
        ]
        
        for field in optional_fields:
            if field in product_info and product_info[field]:
                cleaned[field] = escape(str(product_info[field]).strip())
            else:
                cleaned[field] = ''
        
        return cleaned
    
    @staticmethod
    def validate_parameters(length: str, tone: str, platform: Optional[str] = None) -> bool:
        """Validate prompt parameters"""
        valid_lengths = ['short', 'medium', 'long']
        valid_tones = list(PromptTemplates.TONES.keys())
        valid_platforms = ['instagram', 'facebook', 'tiktok', 'twitter']
        
        if length not in valid_lengths:
            raise ValueError(f"Length must be one of: {valid_lengths}")
        
        if tone not in valid_tones:
            raise ValueError(f"Tone must be one of: {valid_tones}")
        
        if platform and platform not in valid_platforms:
            raise ValueError(f"Platform must be one of: {valid_platforms}")
        
        return True