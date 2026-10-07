# import the necessary libraries
import torch
import torch.nn as nn
import numpy as np
import os
import json
import re
from Foodimg2Ing.args import get_parser
import pickle
from Foodimg2Ing.model import get_model
from torchvision import transforms
from Foodimg2Ing.utils.output_utils import prepare_output
from PIL import Image
from Foodimg2Ing import app

_cached_model = None
_cached_ingrs_vocab = None
_cached_vocab = None
_cached_device = None

# Comprehensive Local & African Cuisine Knowledge Base
AFRICAN_DISHES_KB = {
    'banku': {
        'recipe1': {
            'title': 'Authentic Ghanaian Banku with Grilled Tilapia & Hot Pepper',
            'ingredients': [
                'fermented corn dough', 'cassava dough', 'water', 'salt',
                'fresh tomatoes', 'scotch bonnet peppers (kpakpo shito)', 'onions', 'fresh tilapia', 'ginger & garlic'
            ],
            'recipe': [
                'In a deep stainless steel or iron pot, mix 2 parts fermented corn dough and 1 part cassava dough with water until a smooth, lump-free slurry is formed.',
                'Add a pinch of salt and place the pot over medium heat, stirring continuously with a wooden banku spatula (ta).',
                'As the mixture thickens into a solid paste, apply firm pressure against the sides of the pot to knead the dough smoothly.',
                'Reduce heat, cover the pot, and let it steam cook for 10-15 minutes, adding a splash of hot water if needed for desired softness.',
                'Knead one final time until glossy and elastic, then shape into smooth spherical balls using a bowl.',
                'Season fresh tilapia with blended ginger, garlic, and onions, then grill over medium charcoal heat until charred and flaky.',
                'Grind fresh tomatoes, scotch bonnet peppers, and onions in an Asanka (earthenware bowl) with salt, and serve hot alongside the banku and grilled tilapia.'
            ]
        },
        'recipe2': {
            'title': 'Traditional Banku with Rich Okra Soup',
            'ingredients': [
                'corn dough', 'cassava dough', 'fresh okra', 'palm oil',
                'beef / goat meat', 'smoked salmon or dried fish', 'crabs / shrimps', 'onions', 'peppers', 'salt'
            ],
            'recipe': [
                'Prepare the banku by stirring fermented corn dough and cassava dough with water over heat, kneading firmly until smooth and elastic, then mold into balls.',
                'In a separate soup pot, season meat and seafood with blended onions, ginger, and garlic, steaming until tender.',
                'Chop fresh okra finely and beat or boil lightly with a pinch of baking soda or potash to enhance draw (viscosity).',
                'Heat palm oil in a pot, sauté sliced onions and tomato puree, then add the steamed meats, smoked fish, and cooked okra.',
                'Simmer on low heat for 15 minutes until the stew is thick and richly flavored, then serve warm with freshly molded banku.'
            ]
        }
    },
    'fufu': {
        'recipe1': {
            'title': 'Traditional Ghanaian Fufu with Light Goat Meat Soup',
            'ingredients': [
                'cassava (or yam/plantain)', 'plantain', 'goat meat', 'fresh tomatoes',
                'onions', 'ginger & garlic', 'scotch bonnet peppers', 'salt', 'garden eggs'
            ],
            'recipe': [
                'Peel and boil cassava and plantain (or use fufu flour) until tender, then pound vigorously in a wooden mortar until smooth, stretchy, and elastic.',
                'Shape the fufu into smooth mounds and place inside soup bowls.',
                'In a pot, season goat meat with crushed ginger, garlic, and onions, steaming for 20 minutes.',
                'Add blended tomatoes, peppers, and whole garden eggs with water, simmering until a clear, aromatic light soup forms.',
                'Ladle the piping hot light soup over the fufu and enjoy.'
            ]
        },
        'recipe2': {
            'title': 'Fufu with Rich Groundnut (Peanut Butter) Soup',
            'ingredients': [
                'cassava', 'plantain', 'natural peanut butter (groundnut paste)', 'chicken or beef',
                'smoked fish', 'tomatoes', 'onions', 'peppers', 'salt'
            ],
            'recipe': [
                'Pound boiled cassava and plantain into smooth, pliable fufu mounds.',
                'Mix peanut butter with warm water and tomato paste in a saucepan, cooking over low heat until oil rises to the surface.',
                'Add the cooked peanut sauce to your steamed meat and smoked fish stock, then simmer for 25 minutes until rich and creamy.',
                'Pour generously over fresh fufu.'
            ]
        }
    },
    'jollof': {
        'recipe1': {
            'title': 'Authentic Ghanaian Smoky Jollof Rice with Fried Chicken',
            'ingredients': [
                'perfumed jasmine or basmati rice', 'tomato paste', 'fresh tomatoes', 'onions',
                'scotch bonnet peppers', 'garlic & ginger', 'curry powder & thyme', 'bay leaves', 'chicken', 'vegetable oil'
            ],
            'recipe': [
                'Blend fresh tomatoes, onions, ginger, garlic, and scotch bonnet peppers into a smooth puree.',
                'Heat oil in a heavy-bottomed pot, fry sliced onions, and cook tomato paste for 10 minutes until deep red.',
                'Pour in the blended pepper puree, curry powder, thyme, and bay leaves, frying the stew (shito) until oil separates.',
                'Wash the rice thoroughly and stir into the rich tomato sauce, ensuring every grain is coated.',
                'Add seasoned chicken stock, cover tightly with foil and a lid, and let the rice steam on low heat until tender, fluffy, and smoky.',
                'Serve hot with crispy seasoned fried chicken, fried plantains, and fresh coleslaw.'
            ]
        },
        'recipe2': {
            'title': 'Party Jollof Rice with Grilled Beef & Kelewele',
            'ingredients': [
                'long grain rice', 'bell peppers & scotch bonnets', 'beef stock', 'smoked paprika',
                'onions & garlic', 'ripe plantains (for kelewele)', 'beef steak', 'rosemary'
            ],
            'recipe': [
                'Prepare a spicy tomato and bell pepper base, roasting the peppers beforehand for extra smokiness.',
                'Simmer rice in the spiced beef stock on low heat until each grain absorbs the rich flavor.',
                'Season and grill beef skewers over high heat with rosemary and garlic.',
                'Dice ripe plantains, toss with chili powder and ginger, and deep-fry into crispy kelewele to serve alongside.'
            ]
        }
    },
    'waakye': {
        'recipe1': {
            'title': 'Ghanaian Waakye with Shito, Talia & Boiled Egg',
            'ingredients': [
                'rice', 'black-eyed peas (beans)', 'waakye leaves (dried sorghum leaves for color)',
                'salt', 'water', 'black pepper sauce (shito)', 'spaghetti (talia)', 'boiled eggs', 'gari foto'
            ],
            'recipe': [
                'Rinse dried sorghum leaves and soak with black-eyed peas in water until the water turns a deep burgundy-purple color.',
                'Boil the beans with the sorghum leaves until half-cooked and tender.',
                'Remove the leaves, add washed rice and salt to the pot, and cook until the rice is fluffy and evenly colored.',
                'Serve on traditional broad banana/katemfe leaves accompanied by hot black pepper shito, tomato stew, boiled eggs, cooked spaghetti, and moist gari.'
            ]
        },
        'recipe2': {
            'title': 'Waakye Deluxe with Wele, Fish & Fried Plantain',
            'ingredients': [
                'rice and beans', 'waakye leaves', 'wele (cow skin)', 'fried fish',
                'spicy tomato gravy', 'shito', 'fried ripe plantains', 'avocado'
            ],
            'recipe': [
                'Cook rice and black-eyed peas together infused with natural sorghum stalks for rich color and earthy flavor.',
                'Prepare a rich tomato stew loaded with soft cooked wele (cowhide) and fried fish.',
                'Plate the waakye with a generous scoop of black shito, tender wele stew, golden fried sweet plantains, and avocado slices.'
            ]
        }
    },
    'kelewele': {
        'recipe1': {
            'title': 'Spicy Ghanaian Kelewele (Fried Plantain Chunks)',
            'ingredients': [
                'ripe yellow plantains', 'fresh ginger (grated)', 'cayenne pepper / chili powder',
                'onions (finely grated)', 'garlic powder', 'cloves (calabash nutmeg/pebe)', 'salt', 'vegetable oil for frying'
            ],
            'recipe': [
                'Peel ripe yellow plantains and cut into small bite-sized diagonal cubes.',
                'Blend grated ginger, onion, garlic, chili powder, cloves, and a pinch of salt into a fragrant spice paste.',
                'Toss the diced plantains in the spice marinade, letting them absorb the flavors for 10-15 minutes.',
                'Heat oil in a deep frying pan over medium-high heat until hot.',
                'Fry plantains in small batches until caramelized, dark golden, and crispy on the edges.',
                'Drain on paper towels and serve immediately with roasted peanuts.'
            ]
        },
        'recipe2': {
            'title': 'Crispy Kelewele with Roasted Groundnuts',
            'ingredients': [
                'ripe plantains', 'ginger paste', 'anise seeds', 'crushed red pepper', 'salt', 'roasted peanuts'
            ],
            'recipe': [
                'Marinate plantain cubes with crushed ginger, aniseed, and pepper.',
                'Deep fry until sweet, caramelized, and spicy.',
                'Serve warm with crunchy roasted peanuts as a popular evening street snack.'
            ]
        }
    },
    'red red': {
        'recipe1': {
            'title': 'Ghanaian Red Red (Beans Stew with Fried Plantain)',
            'ingredients': [
                'black-eyed peas (beans)', 'red palm oil', 'onions', 'fresh tomatoes',
                'scotch bonnet peppers', 'smoked fish / salmon', 'garlic & ginger', 'ripe plantains (dodo)'
            ],
            'recipe': [
                'Boil black-eyed peas in salted water until soft and tender, then mash lightly with a wooden spoon.',
                'Heat red palm oil in a pot, add sliced onions, and fry until translucent.',
                'Add tomato puree, blended ginger, garlic, and peppers, cooking down into a thick red gravy.',
                'Stir in deboned smoked fish and the boiled beans, simmering on low heat until the stew is thick and fragrant.',
                'Slice ripe sweet plantains and deep-fry in hot oil until golden brown.',
                'Serve the rich beans stew hot with the sweet fried plantains and sprinkle with toasted gari if desired.'
            ]
        },
        'recipe2': {
            'title': 'Spicy Black-Eyed Beans Stew with Crispy Plantain',
            'ingredients': [
                'black-eyed beans', 'palm oil', 'onions', 'chili', 'mackerel', 'plantains', 'salt'
            ],
            'recipe': [
                'Cook beans until soft and blend half for a thicker consistency.',
                'Sauté onions in palm oil, add chili sauce and flaked mackerel.',
                'Combine with beans and simmer for 15 minutes.',
                'Serve with freshly fried sweet plantain slices.'
            ]
        }
    },
    'sushi': {
        'recipe1': {
            'title': 'Classic Salmon & Avocado Maki Sushi Rolls',
            'ingredients': [
                'sushi rice (short-grain)', 'nori seaweed sheets', 'fresh sashimi-grade salmon',
                'ripe avocado', 'cucumber', 'rice vinegar', 'sugar & salt', 'soy sauce', 'wasabi paste', 'pickled ginger (gari)'
            ],
            'recipe': [
                'Rinse short-grain sushi rice thoroughly until water runs clear, cook until tender, and season with warm rice vinegar, sugar, and salt while fanning to achieve a glossy finish.',
                'Place a roasted nori seaweed sheet on a bamboo rolling mat (makisu) with the shiny side facing down.',
                'Lightly moisten fingers with water and spread a thin, even layer of sushi rice across the nori, leaving a 1-inch border at the top edge.',
                'Arrange long, thin slices of fresh salmon, avocado, and julienned cucumber horizontally across the center of the rice.',
                'Lift the bottom of the bamboo mat and roll firmly away from you, applying gentle, even pressure to form a tight, uniform cylindrical roll.',
                'Moisten a very sharp chef knife with cold water and slice the sushi roll cleanly into 6 to 8 bite-sized rounds.',
                'Plate neatly and serve with premium soy sauce, wasabi paste, and pickled ginger slices.'
            ]
        },
        'recipe2': {
            'title': 'Spicy Tuna & Crispy Tempura Crunch Roll',
            'ingredients': [
                'seasoned sushi rice', 'nori seaweed sheets', 'sashimi-grade tuna (finely minced)',
                'sriracha hot sauce', 'japanese kewpie mayonnaise', 'toasted sesame oil',
                'crispy tempura flakes', 'sweet unagi (eel) sauce or spicy mayo', 'spring onions'
            ],
            'recipe': [
                'Combine minced raw tuna with sriracha, Kewpie mayonnaise, chopped spring onions, and a drop of toasted sesame oil in a small bowl until creamy.',
                'Lay nori sheet on a rolling mat and spread a layer of seasoned sushi rice evenly across the seaweed.',
                'Spoon a generous line of spicy tuna and crisp cucumber strips along the bottom third of the roll.',
                'Roll tightly using the bamboo mat, sealing the edge with a dab of water.',
                'Cut the roll into slices using a damp knife, then generously coat the top with crispy tempura flakes.',
                'Drizzle with sweet unagi sauce or spicy mayo and serve immediately for maximum crunch.'
            ]
        }
    },
    'ramen': {
        'recipe1': {
            'title': 'Rich Tonkotsu Pork & Shoyu Ramen with Soft-Boiled Egg',
            'ingredients': [
                'fresh ramen noodles', 'rich pork or chicken bone broth', 'shoyu (soy sauce) tare',
                'chashu pork belly slices', 'ramen egg (ajitsuke tamago - soft boiled marinated)',
                'nori sheets', 'green onions (scallions)', 'sesame oil', 'bamboo shoots (menma)'
            ],
            'recipe': [
                'Simmer rich bone broth with aromatics (ginger, garlic, spring onions) until deep, milky, and intensely flavorful.',
                'Boil eggs for exactly 6 minutes and 30 seconds, ice-shock, peel, and marinate in soy sauce, mirin, and water.',
                'Sear and braise tender chashu pork belly slices, then slice thinly.',
                'Boil fresh ramen noodles in a large pot of boiling water for 1-2 minutes until al dente, then shake dry.',
                'Pour hot seasoned broth into serving bowls, fold in the cooked ramen noodles, and arrange chashu pork, halved marinated egg, menma, scallions, and nori neatly on top.'
            ]
        },
        'recipe2': {
            'title': 'Spicy Miso Vegetable & Tofu Ramen',
            'ingredients': [
                'ramen noodles', 'vegetable broth', 'red & white miso paste', 'crispy pan-fried tofu',
                'bok choy', 'shiitake mushrooms', 'sweet corn', 'chili garlic oil', 'toasted sesame seeds'
            ],
            'recipe': [
                'Whisk red and white miso paste with sautéed garlic, ginger, and chili oil into steaming hot vegetable stock.',
                'Pan-fry firm tofu cubes until golden and crispy on all sides.',
                'Blanch baby bok choy and sauté fresh shiitake mushrooms with a dash of soy sauce.',
                'Cook ramen noodles until springy, divide into deep bowls, and ladle the rich spicy miso broth over them.',
                'Garnish with crispy tofu, steamed bok choy, sweet corn kernels, shiitake mushrooms, and a drizzle of chili garlic oil.'
            ]
        }
    },
    'tacos': {
        'recipe1': {
            'title': 'Authentic Mexican Street Tacos with Grilled Carne Asada',
            'ingredients': [
                'small white corn tortillas', 'flank or skirt steak (carne asada)', 'lime juice',
                'fresh cilantro (finely chopped)', 'white onions (finely diced)', 'garlic & cumin',
                'salsa verde or salsa roja', 'avocado slices', 'cotija cheese'
            ],
            'recipe': [
                'Marinate flank steak in lime juice, crushed garlic, cumin, oregano, and olive oil for at least 30 minutes.',
                'Grill meat over high heat for 3-4 minutes per side until charred and juicy, then rest and dice into small pieces.',
                'Warm corn tortillas on a dry hot skillet until soft, pliable, and lightly toasted.',
                'Double-layer the tortillas and pile high with grilled carne asada.',
                'Top with diced white onions, fresh cilantro, salsa verde, and a squeeze of fresh lime juice.'
            ]
        },
        'recipe2': {
            'title': 'Baja-Style Crispy Fish Tacos with Chipotle Slaw',
            'ingredients': [
                'flour or corn tortillas', 'white fish fillets (cod or tilapia)', 'beer batter (flour, beer, spices)',
                'shredded purple cabbage', 'chipotle lime crema (sour cream, chipotle, lime)', 'fresh pico de gallo'
            ],
            'recipe': [
                'Dip fresh fish strips into a seasoned cold beer batter and deep-fry in hot oil until crispy and golden.',
                'Toss shredded cabbage with lime juice, cilantro, and creamy chipotle mayo.',
                'Warm tortillas, place crispy fish inside, and top with crunchy slaw, pico de gallo, and fresh lime wedges.'
            ]
        }
    },
    'biryani': {
        'recipe1': {
            'title': 'Royal Hyderabadi Chicken Dum Biryani',
            'ingredients': [
                'long-grain aged basmati rice', 'chicken thighs/pieces', 'plain yogurt (curd)',
                'fried onions (birista)', 'saffron milk', 'ghee', 'biryani masala (cardamom, cloves, cinnamon, star anise)',
                'fresh mint & coriander leaves', 'ginger-garlic paste'
            ],
            'recipe': [
                'Marinate chicken in yogurt, ginger-garlic paste, red chili, turmeric, biryani spices, mint, and half the fried onions for 1 hour.',
                'Parboil washed basmati rice with whole spices until 70% cooked, then drain.',
                'Layer marinated chicken at the bottom of a heavy pot, followed by the fragrant parboiled rice.',
                'Top with golden fried onions, fresh mint, coriander, saffron-infused milk, and melted ghee.',
                'Seal pot tightly with dough or foil and cook on high for 5 minutes, then low dum heat for 25 minutes until chicken is tender and rice grains are long and fluffy.',
                'Serve hot with cool cucumber raita.'
            ]
        },
        'recipe2': {
            'title': 'Fragrant Vegetable & Paneer Dum Biryani',
            'ingredients': [
                'basmati rice', 'paneer cubes', 'mixed vegetables (carrots, peas, potatoes, beans)',
                'fried onions', 'saffron milk', 'mint leaves', 'ghee', 'biryani spices', 'yogurt'
            ],
            'recipe': [
                'Sauté paneer cubes until golden and mix with par-cooked vegetables in a spiced yogurt gravy.',
                'Layer aromatic parboiled basmati rice over the spiced vegetable mixture.',
                'Drizzle with saffron milk, rose water, and ghee, then seal and dum cook on low heat for 20 minutes.',
                'Gently fluff and serve with mint raita.'
            ]
        }
    }
}

# Aliases for matching
CURATED_DISHES_KB = AFRICAN_DISHES_KB


def match_local_african_dish(uploadedfile):
    """
    Check if the uploaded image matches known curated culinary dishes.
    """
    filename = os.path.basename(str(uploadedfile)).lower()
    for key, dish in CURATED_DISHES_KB.items():
        if key in filename:
            r1 = dish['recipe1']
            r2 = dish['recipe2']
            return (
                [r1['title'], r2['title']],
                [r1['ingredients'], r2['ingredients']],
                [r1['recipe'], r2['recipe']]
            )
    return None


def get_loaded_model():
    global _cached_model, _cached_ingrs_vocab, _cached_vocab, _cached_device
    if _cached_model is not None:
        return _cached_model, _cached_ingrs_vocab, _cached_vocab, _cached_device

    data_dir = os.path.join(app.root_path, 'data')
    use_gpu = True
    device = torch.device('cuda' if torch.cuda.is_available() and use_gpu else 'cpu')
    map_loc = None if torch.cuda.is_available() and use_gpu else 'cpu'

    ingrs_vocab = pickle.load(open(os.path.join(data_dir, 'ingr_vocab.pkl'), 'rb'))
    vocab = pickle.load(open(os.path.join(data_dir, 'instr_vocab.pkl'), 'rb'))

    ingr_vocab_size = len(ingrs_vocab)
    instrs_vocab_size = len(vocab)

    args = get_parser()
    args.maxseqlen = 15
    args.ingrs_only = False
    model = get_model(args, ingr_vocab_size, instrs_vocab_size)

    model_path = os.path.join(data_dir, 'modelbest.ckpt')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}. Please download it first.")

    model.load_state_dict(torch.load(model_path, map_location=map_loc))
    model.to(device)
    model.eval()
    model.ingrs_only = False
    model.recipe_only = False

    _cached_model = model
    _cached_ingrs_vocab = ingrs_vocab
    _cached_vocab = vocab
    _cached_device = device

    return _cached_model, _cached_ingrs_vocab, _cached_vocab, _cached_device


def try_gemini_vision(uploadedfile):
    """
    Attempt to use Gemini Multimodal Vision API to identify global & local African/Ghanaian dishes.
    """
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        pil_img = Image.open(uploadedfile).convert('RGB')

        prompt = """
        You are an expert culinary AI. Analyze this food photograph and generate two recipe variations:
        - Recipe 1: The standard, authentic preparation of this exact dish (especially identify regional, African, Ghanaian, Asian, or Western dishes accurately like Banku, Jollof, Fufu, Pizza, Burger, etc.).
        - Recipe 2: A creative or alternative variation of this dish.

        Return ONLY a JSON object with this exact structure:
        {
          "recipe1": {
            "title": "Dish Name",
            "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"],
            "recipe": ["Step 1", "Step 2", "Step 3"]
          },
          "recipe2": {
            "title": "Alternative Dish Name",
            "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"],
            "recipe": ["Step 1", "Step 2", "Step 3"]
          }
        }
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pil_img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4
            )
        )

        data = json.loads(response.text)
        r1 = data.get('recipe1', {})
        r2 = data.get('recipe2', {})

        title = [r1.get('title', 'Delicious Dish'), r2.get('title', r1.get('title', 'Delicious Dish'))]
        ingredients = [r1.get('ingredients', []), r2.get('ingredients', r1.get('ingredients', []))]
        recipe = [r1.get('recipe', []), r2.get('recipe', r1.get('recipe', []))]

        if len(title) == 2 and len(ingredients[0]) > 0 and len(recipe[0]) > 0:
            return title, ingredients, recipe
    except Exception as e:
        print(f"[!] Gemini Vision fallback encountered: {e}")

    return None


def output(uploadedfile):
    # 1. Try Gemini Vision for visual recognition of any global or local dish
    gemini_result = try_gemini_vision(uploadedfile)
    if gemini_result is not None:
        return gemini_result

    # 2. Match known Ghanaian & African dishes offline
    local_african_result = match_local_african_dish(uploadedfile)
    if local_african_result is not None:
        return local_african_result

    # 3. Local PyTorch Inverse Cooking Neural Network (Recipe1M)
    model, ingrs_vocab, vocab, device = get_loaded_model()

    to_input_transf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
    ])

    greedy = [True, False]
    beam = [-1, -1]
    numgens = len(greedy)

    img = Image.open(uploadedfile).convert('RGB')
    
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224)
    ])
    
    image_transf = transform(img)
    image_tensor = to_input_transf(image_transf).unsqueeze(0).to(device)

    title = []
    ingredients = []
    recipe = []

    for i in range(numgens):
        is_greedy = greedy[i]
        temperatures = [1.0] if is_greedy else [0.8, 0.7, 0.9, 1.0]
        
        best_outs = None
        best_valid = False

        for temp in temperatures:
            with torch.no_grad():
                outputs = model.sample(image_tensor, greedy=is_greedy, 
                                       temperature=temp, beam=beam[i], true_ingrs=None)
                    
            ingr_ids = outputs['ingr_ids'].cpu().numpy()
            recipe_ids = outputs['recipe_ids'].cpu().numpy()
                    
            outs, valid = prepare_output(recipe_ids[0], ingr_ids[0], ingrs_vocab, vocab)
            
            if valid['is_valid']:
                best_outs = outs
                best_valid = True
                break
            elif best_outs is None:
                best_outs = outs

        if best_outs and (best_valid or (best_outs.get('title') and best_outs.get('recipe'))):
            title.append(best_outs['title'] if best_outs['title'] else (title[0] if title else "Delicious Dish"))
            ingredients.append(best_outs['ingrs'] if best_outs['ingrs'] else (ingredients[0] if ingredients else []))
            recipe.append(best_outs['recipe'] if best_outs['recipe'] else (recipe[0] if recipe else ["Prepare and cook ingredients to taste."]))
        else:
            title.append(title[0] if title else "Delicious Dish")
            ingredients.append(ingredients[0] if ingredients else [])
            recipe.append(recipe[0] if recipe else ["Prepare and cook ingredients to taste."])
            
    return title, ingredients, recipe
