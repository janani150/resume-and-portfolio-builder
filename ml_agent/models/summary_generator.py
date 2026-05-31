# models/summary_generator.py
"""
Model: Fine-tuned GPT-2 (small — 117M params, runs on CPU)
Task: Generate professional resume summary from bullet points
Training: Resume summaries dataset (~500 examples)
"""
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset
from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments

# ── Step 1: Prepare Training Data ─────────────────────
def prepare_training_data(output_path="data/processed/summaries.txt"):
    """
    Create training data format:
    INPUT: skills + role + experience
    OUTPUT: professional summary
    """
    examples = [
        "INPUT: Python, FastAPI, MongoDB | Role: Backend Developer | Exp: Fresher
OUTPUT: A passionate Backend Developer skilled in Python and FastAPI, with hands-on experience building RESTful APIs and working with MongoDB. Quick learner eager to contribute to fast-paced development teams.
###",
        "INPUT: React, Node.js, SQL | Role: Full Stack Developer | Exp: 1 year
OUTPUT: Results-driven Full Stack Developer with 1 year of experience in React and Node.js. Proven ability to build end-to-end web applications with clean, maintainable code and strong UI/UX sensibility.
###",
        # Add more examples...
    ]
    with open(output_path, 'w') as f:
        f.write('
'.join(examples))
    print(f"Training data saved to {output_path}")

# ── Step 2: Fine-tune GPT-2 ───────────────────────────
def finetune_gpt2(data_path="data/processed/summaries.txt"):
    model_name = "gpt2"  # smallest GPT-2
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    model = GPT2LMHeadModel.from_pretrained(model_name)

    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=data_path,
        block_size=128
    )
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False
    )

    training_args = TrainingArguments(
        output_dir="data/models/gpt2-resume",
        num_train_epochs=5,
        per_device_train_batch_size=4,
        save_steps=100,
        logging_steps=10,
        learning_rate=5e-5,
        warmup_steps=50,
        prediction_loss_only=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=dataset,
    )

    print("Starting GPT-2 fine-tuning...")
    trainer.train()
    model.save_pretrained("data/models/gpt2-resume")
    tokenizer.save_pretrained("data/models/gpt2-resume")
    print("Fine-tuning complete!")

# ── Step 3: Generate Summary ───────────────────────────
def generate_summary(skills: list, role: str, experience: str = "Fresher") -> str:
    tokenizer = GPT2Tokenizer.from_pretrained("data/models/gpt2-resume")
    model = GPT2LMHeadModel.from_pretrained("data/models/gpt2-resume")
    model.eval()

    prompt = f"INPUT: {', '.join(skills)} | Role: {role} | Exp: {experience}
OUTPUT:"
    inputs = tokenizer.encode(prompt, return_tensors='pt')

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=100,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    summary = generated.split("OUTPUT:")[-1].split("###")[0].strip()
    return summary

if __name__ == "__main__":
    prepare_training_data()
    finetune_gpt2()
    summary = generate_summary(
        skills=["Python", "FastAPI", "React", "MongoDB"],
        role="Full Stack Developer",
        experience="Fresher"
    )
    print("Generated Summary:", summary)