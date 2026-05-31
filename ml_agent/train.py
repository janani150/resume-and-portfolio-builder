# train.py — Run this ONCE to train all models
"""
Master training script
Run: python train.py
Takes ~10-20 mins depending on your machine
"""
import os
from models.skill_extractor import load_data, train_classifier, save_model
from models.summary_generator import prepare_training_data, finetune_gpt2

def train_all():
    os.makedirs("data/models", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    print("=" * 50)
    print("Step 1/3: Training Skill Extractor...")
    print("=" * 50)
    df = load_data("data/raw/resume_dataset.csv")
    model, vectorizer = train_classifier(df)
    save_model(model, vectorizer)

    print("=" * 50)
    print("Step 2/3: Preparing GPT-2 Training Data...")
    print("=" * 50)
    prepare_training_data()

    print("=" * 50)
    print("Step 3/3: Fine-tuning GPT-2...")
    print("=" * 50)
    finetune_gpt2()

    print("=" * 50)
    print("All models trained! Run the API server now.")
    print("=" * 50)

if __name__ == "__main__":
    train_all()