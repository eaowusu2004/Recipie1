# import the necessary libraries
import torch
import torch.nn as nn
import numpy as np
import os
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


def output(uploadedfile):
    model, ingrs_vocab, vocab, device = get_loaded_model()

    to_input_transf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
    ])

    greedy = [True, False]
    beam = [-1, -1]
    temperature = 1.0
    numgens = len(greedy)

    img = Image.open(uploadedfile).convert('RGB')
    
    show_anyways = False
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
        with torch.no_grad():
            outputs = model.sample(image_tensor, greedy=greedy[i], 
                                   temperature=temperature, beam=beam[i], true_ingrs=None)
                
        ingr_ids = outputs['ingr_ids'].cpu().numpy()
        recipe_ids = outputs['recipe_ids'].cpu().numpy()
                
        outs, valid = prepare_output(recipe_ids[0], ingr_ids[0], ingrs_vocab, vocab)
            
        if valid['is_valid'] or show_anyways:
            title.append(outs['title'])
            ingredients.append(outs['ingrs'])
            recipe.append(outs['recipe'])
        else:
            title.append("Not a valid recipe!")
            ingredients.append([])
            recipe.append("Reason: " + valid['reason'])
            
    return title, ingredients, recipe

