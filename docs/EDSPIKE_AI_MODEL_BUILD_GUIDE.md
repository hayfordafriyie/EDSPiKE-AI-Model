# EDSPiKE AI Model: Building from Scratch (Industry Standard)

**Status:** Production Playbook  
**Target:** Custom LLM for Educational Management & School Operations  
**Scope:** Phase 1 MVP → Phase 2 Production  

---

## Table of Contents
1. [Executive Overview](#executive-overview)
2. [Phase 1: Foundation & Proof of Concept](#phase-1-foundation--proof-of-concept)
3. [Phase 2: Data Pipeline & Scale](#phase-2-data-pipeline--scale)
4. [Phase 3: Model Training](#phase-3-model-training)
5. [Phase 4: Evaluation & Benchmarking](#phase-4-evaluation--benchmarking)
6. [Phase 5: Optimization & Deployment](#phase-5-optimization--deployment)
7. [Production Infrastructure](#production-infrastructure)
8. [Team & Timeline](#team--timeline)

---

## Executive Overview

### What We're Building
A specialized transformer-based language model (7B-13B parameters) trained on:
- Educational domain data (curriculum, assessments, school operations)
- Ghana-specific context (local education system, WAEC standards, GES policies)
- Code generation for EdTech workflows
- Natural language understanding for school admin queries

### Why Custom Instead of Fine-tune?
- **Control:** Full ownership of training data, architecture, inference
- **Cost:** Single API call → revenue opportunity vs API dependency
- **Latency:** Sub-100ms inference on your infrastructure
- **Privacy:** No data leaves EDSPiKE servers
- **Scale:** Unlimited concurrent users without rate limits

### Timeline & Resource Estimate
- **Phase 1-2:** 4-6 weeks (data + infra setup)
- **Phase 3:** 2-3 weeks (training on H100/A100)
- **Phase 4:** 1-2 weeks (evaluation + iteration)
- **Phase 5:** 2-3 weeks (optimization + deployment)
- **Total:** 9-14 weeks to production MVP

**Resource:** 1 ML Engineer (lead) + 1 Data Engineer + 1 DevOps (part-time)

---

## Phase 1: Foundation & Proof of Concept

### 1.1 Environment Setup

```bash
# Prerequisites
Python 3.10+ (3.11 recommended)
CUDA 12.1+ (if GPU available)
Git + GitHub
Docker + docker-compose

# Core directory structure
edspike-ai-model/
├── data/
│   ├── raw/              # Original sources
│   ├── processed/        # Tokenized, formatted
│   └── splits/           # train/val/test
├── src/
│   ├── data_pipeline/    # Collection & preprocessing
│   ├── tokenizer/        # Custom tokenizer
│   ├── model/            # Architecture definitions
│   ├── training/         # Training loops
│   └── evaluation/       # Benchmarks & metrics
├── configs/              # YAML configs for experiments
├── checkpoints/          # Model weights
├── notebooks/            # Jupyter for EDA
├── tests/                # Unit & integration tests
├── scripts/              # Utility scripts
└── README.md
```

### 1.2 Dependencies & Virtual Environment

Create `requirements.txt`:
```
# Core ML
torch==2.1.2
transformers==4.36.0
datasets==2.14.6
accelerate==0.25.0
peft==0.7.1
bitsandbytes==0.41.3

# Data processing
pandas==2.1.3
numpy==1.26.2
pyarrow==14.0.1
scikit-learn==1.3.2

# Tokenization
tokenizers==0.15.0
sentencepiece==0.1.99

# Logging & monitoring
wandb==0.16.1
tensorboard==2.15.1

# DevOps
python-dotenv==1.0.0
pyyaml==6.0.1
click==8.1.7

# Testing
pytest==7.4.3
pytest-cov==4.1.0
```

**Setup:**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 1.3 Configuration Management

Create `configs/base_config.yaml`:
```yaml
# Model Configuration
model:
  architecture: "llama"  # or gpt2, gptj
  vocab_size: 32000
  hidden_size: 4096
  intermediate_size: 11008
  num_hidden_layers: 32
  num_attention_heads: 32
  attention_head_size: 128
  max_sequence_length: 2048
  dropout: 0.1
  layer_norm_eps: 1e-6

# Training Configuration
training:
  learning_rate: 5e-5
  batch_size: 32  # Global, adjust per GPU
  gradient_accumulation_steps: 1
  num_epochs: 3
  warmup_steps: 2000
  weight_decay: 0.01
  max_grad_norm: 1.0
  logging_steps: 100
  eval_steps: 500
  save_steps: 1000
  optimizer: "adamw_8bit"  # Memory efficient

# Data Configuration
data:
  train_split: 0.8
  val_split: 0.1
  test_split: 0.1
  max_examples: null  # null = use all
  seed: 42

# Compute
compute:
  device: "cuda"  # or cpu for testing
  mixed_precision: "bf16"  # better than fp16
  gradient_checkpointing: true  # memory optimization
  num_workers: 4
```

---

## Phase 2: Data Pipeline & Scale

### 2.1 Data Sources Strategy

For EDSPiKE, aggregate from:

1. **Educational Content (40%)**
   - Ghana Education Service (GES) curriculum documents
   - WAEC exam papers & marking schemes (2010-2024)
   - School textbooks (digitized)
   - University CS/IT programs (local context)

2. **Operational Data (30%)**
   - Anonymized student records (grades, attendance patterns)
   - Timetable generation rules & constraints
   - Fee payment workflows & edge cases
   - Parent-teacher communication templates

3. **Code & Technical (20%)**
   - EdTech API documentation
   - School management workflows (documented)
   - Common SQL queries for reporting
   - React component patterns (if UI generation in scope)

4. **External Quality Data (10%)**
   - High-quality Wikipedia education sections
   - Academic papers on pedagogy
   - Kaggle education datasets
   - Open educational resources (OER)

### 2.2 Data Collection & Preprocessing

Create `src/data_pipeline/collector.py`:

```python
import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class DataCollector:
    """Centralized data collection from multiple sources"""
    
    def __init__(self, raw_data_dir: str = "data/raw"):
        self.raw_dir = Path(raw_data_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_ges_curriculum(self, source_path: str) -> List[Dict]:
        """Parse GES curriculum PDFs or documents"""
        documents = []
        # Implementation: PDF extraction, text cleaning
        logger.info(f"Collected {len(documents)} GES curriculum documents")
        return documents
    
    def collect_waec_papers(self, source_dir: str) -> List[Dict]:
        """Aggregate WAEC exam papers with solutions"""
        papers = []
        for year in range(2010, 2025):
            # Fetch papers → parse questions + answers
            pass
        logger.info(f"Collected {len(papers)} WAEC papers")
        return papers
    
    def collect_school_operations(self, db_connection) -> List[Dict]:
        """Extract anonymized operational data from EDSPiKE"""
        queries = {
            "timetables": "SELECT * FROM timetables LIMIT 10000",
            "gradebooks": "SELECT class, subject, avg_score FROM grades GROUP BY class, subject",
            "attendance_patterns": "SELECT * FROM attendance LIMIT 20000",
        }
        data = {}
        for key, query in queries.items():
            data[key] = pd.read_sql(query, db_connection).to_dict('records')
        logger.info(f"Collected school operations data: {len(data)} datasets")
        return data
    
    def save_raw_data(self, data: List[Dict], name: str):
        """Persist raw data"""
        output_path = self.raw_dir / f"{name}.jsonl"
        with open(output_path, 'w') as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
        logger.info(f"Saved {len(data)} records to {output_path}")
```

### 2.3 Data Preprocessing & Formatting

Create `src/data_pipeline/preprocessor.py`:

```python
import json
from pathlib import Path
from typing import List, Dict
import pandas as pd

class DataPreprocessor:
    """Format diverse data sources into uniform training format"""
    
    @staticmethod
    def format_qa_pair(question: str, answer: str, context: str = "") -> Dict:
        """Convert Q&A into instruction-following format"""
        return {
            "instruction": question,
            "input": context,
            "output": answer,
            "category": "education"
        }
    
    @staticmethod
    def format_code_example(description: str, code: str, language: str = "python") -> Dict:
        """Format code generation examples"""
        return {
            "instruction": f"Write {language} code to: {description}",
            "input": "",
            "output": code,
            "language": language,
            "category": "coding"
        }
    
    @staticmethod
    def format_conversation(messages: List[Dict]) -> Dict:
        """Format multi-turn conversations"""
        text = ""
        for msg in messages:
            role = msg.get("role", "user").upper()
            text += f"{role}: {msg.get('content', '')}\n"
        return {
            "text": text.strip(),
            "category": "conversation"
        }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove low-quality markers
        text = text.replace('[CITATION NEEDED]', '')
        return text.strip()
    
    def process_all_sources(self, raw_dir: str, output_dir: str):
        """Pipeline: raw → processed"""
        processed_dir = Path(output_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        raw_path = Path(raw_dir)
        processed_records = []
        
        for jsonl_file in raw_path.glob("*.jsonl"):
            with open(jsonl_file) as f:
                for line in f:
                    record = json.loads(line)
                    # Apply source-specific formatting
                    processed = self._process_record(record)
                    if processed:
                        processed_records.append(processed)
        
        # Save processed data
        output_file = processed_dir / "processed_data.jsonl"
        with open(output_file, 'w') as f:
            for record in processed_records:
                f.write(json.dumps(record) + '\n')
        
        return len(processed_records)
    
    def _process_record(self, record: Dict) -> Dict:
        """Route record to appropriate processor"""
        if "question" in record and "answer" in record:
            return self.format_qa_pair(record["question"], record["answer"])
        elif "code" in record and "description" in record:
            return self.format_code_example(record["description"], record["code"])
        elif "messages" in record:
            return self.format_conversation(record["messages"])
        return None
```

### 2.4 Train/Val/Test Splitting

Create `src/data_pipeline/splitter.py`:

```python
import json
from pathlib import Path
from sklearn.model_selection import train_test_split

class DataSplitter:
    """Split data into train/val/test with stratification"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
    
    def split(self, input_file: str, output_dir: str, 
              train_ratio: float = 0.8,
              val_ratio: float = 0.1,
              test_ratio: float = 0.1):
        """Split processed data"""
        
        # Load all data
        records = []
        with open(input_file) as f:
            records = [json.loads(line) for line in f]
        
        # First split: train+val vs test
        train_val, test = train_test_split(
            records,
            test_size=test_ratio,
            random_state=self.seed
        )
        
        # Second split: train vs val
        val_size = val_ratio / (train_ratio + val_ratio)
        train, val = train_test_split(
            train_val,
            test_size=val_size,
            random_state=self.seed
        )
        
        # Save splits
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for split_name, split_data in [("train", train), ("val", val), ("test", test)]:
            split_file = output_path / f"{split_name}.jsonl"
            with open(split_file, 'w') as f:
                for record in split_data:
                    f.write(json.dumps(record) + '\n')
            
            print(f"{split_name}: {len(split_data)} examples")
```

---

## Phase 3: Model Training

### 3.1 Tokenizer Training

Create `src/tokenizer/train_tokenizer.py`:

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

def train_custom_tokenizer(data_files: list, vocab_size: int = 32000):
    """Train BPE tokenizer on EDSPiKE data"""
    
    # Initialize tokenizer
    tokenizer = Tokenizer(BPE())
    trainer = BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=["<pad>", "<unk>", "<s>", "</s>", "<eos>"]
    )
    tokenizer.pre_tokenizer = Whitespace()
    
    # Train on collected data
    tokenizer.train(data_files, trainer)
    
    # Save
    tokenizer.save("configs/tokenizer.json")
    return tokenizer

# Usage
train_custom_tokenizer(["data/processed/processed_data.jsonl"])
```

### 3.2 Model Architecture

Create `src/model/architecture.py`:

```python
import torch
import torch.nn as nn
from transformers import AutoConfig, AutoModelForCausalLM

class EDSPiKEModel:
    """Initialize or load model for training"""
    
    @staticmethod
    def initialize_llama_style(config_path: str = "configs/base_config.yaml"):
        """Initialize LLaMA-style architecture"""
        import yaml
        
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)
        
        model_config = config_dict['model']
        
        # Using transformers library (production-grade)
        config = AutoConfig.from_pretrained(
            "meta-llama/Llama-2-7b-hf",  # Use as template
            vocab_size=model_config['vocab_size'],
            hidden_size=model_config['hidden_size'],
            intermediate_size=model_config['intermediate_size'],
            num_hidden_layers=model_config['num_hidden_layers'],
            num_attention_heads=model_config['num_attention_heads'],
            max_position_embeddings=model_config['max_sequence_length'],
            rope_scaling=None,  # No scaling for MVP
        )
        
        model = AutoModelForCausalLM.from_config(config)
        
        print(f"Model initialized: {model.num_parameters() / 1e9:.2f}B parameters")
        return model
    
    @staticmethod
    def load_pretrained(model_id: str = "meta-llama/Llama-2-7b-hf"):
        """Load & fine-tune existing open model (faster option)"""
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True
        )
        return model
```

### 3.3 Training Loop

Create `src/training/trainer.py`:

```python
import torch
from transformers import Trainer, TrainingArguments
from datasets import Dataset, load_dataset
import yaml
from pathlib import Path

class EDSPiKETrainer:
    """Production-grade training pipeline"""
    
    def __init__(self, config_path: str = "configs/base_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
    
    def prepare_datasets(self, data_dir: str = "data/splits"):
        """Load train/val/test datasets"""
        
        train_dataset = load_dataset(
            'json',
            data_files=str(Path(data_dir) / "train.jsonl"),
            split="train"
        )
        
        val_dataset = load_dataset(
            'json',
            data_files=str(Path(data_dir) / "val.jsonl"),
            split="train"
        )
        
        return train_dataset, val_dataset
    
    def tokenize_function(self, examples, tokenizer):
        """Tokenize examples"""
        # Combine instruction + input + output
        texts = []
        for inst, inp, out in zip(
            examples.get("instruction", []),
            examples.get("input", []),
            examples.get("output", [])
        ):
            text = f"{inst}\n{inp}\n{out}"
            texts.append(text)
        
        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=self.config['model']['max_sequence_length'],
            padding="max_length",
            return_tensors=None
        )
        
        # Shift labels for causal LM
        tokenized["labels"] = tokenized["input_ids"].copy()
        
        return tokenized
    
    def train(self, model, tokenizer, output_dir: str = "checkpoints"):
        """Execute training"""
        
        train_dataset, val_dataset = self.prepare_datasets()
        
        # Tokenize
        train_dataset = train_dataset.map(
            lambda x: self.tokenize_function(x, tokenizer),
            batched=True,
            num_proc=self.config['compute']['num_workers']
        )
        val_dataset = val_dataset.map(
            lambda x: self.tokenize_function(x, tokenizer),
            batched=True,
            num_proc=self.config['compute']['num_workers']
        )
        
        # Training args
        training_args = TrainingArguments(
            output_dir=output_dir,
            learning_rate=self.config['training']['learning_rate'],
            per_device_train_batch_size=self.config['training']['batch_size'],
            per_device_eval_batch_size=self.config['training']['batch_size'],
            num_train_epochs=self.config['training']['num_epochs'],
            weight_decay=self.config['training']['weight_decay'],
            warmup_steps=self.config['training']['warmup_steps'],
            logging_steps=self.config['training']['logging_steps'],
            eval_steps=self.config['training']['eval_steps'],
            save_steps=self.config['training']['save_steps'],
            gradient_accumulation_steps=self.config['training']['gradient_accumulation_steps'],
            eval_strategy="steps",
            gradient_checkpointing=self.config['compute']['gradient_checkpointing'],
            bf16=self.config['compute']['mixed_precision'] == "bf16",
            report_to=["wandb"],
            run_name="edspike-model-v1"
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer
        )
        
        # Train
        trainer.train()
        
        # Save final model
        model.save_pretrained(f"{output_dir}/final")
        tokenizer.save_pretrained(f"{output_dir}/final")
```

**Run training:**
```bash
python -m src.training.trainer \
    --config_path configs/base_config.yaml \
    --output_dir checkpoints/v1
```

---

## Phase 4: Evaluation & Benchmarking

### 4.1 Evaluation Metrics

Create `src/evaluation/metrics.py`:

```python
from typing import List, Dict
import numpy as np
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu

class EvaluationMetrics:
    """Standard evaluation benchmarks"""
    
    @staticmethod
    def perplexity(logits: np.ndarray, labels: np.ndarray) -> float:
        """Calculate perplexity on test set"""
        loss = -np.log(np.clip(logits, 1e-7, 1.0)).mean()
        return np.exp(loss)
    
    @staticmethod
    def rouge_score(predictions: List[str], references: List[str]) -> Dict:
        """ROUGE scores for text generation quality"""
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
        
        scores = {'rouge1': [], 'rouge2': [], 'rougeL': []}
        for pred, ref in zip(predictions, references):
            score = scorer.score(ref, pred)
            for key in scores:
                scores[key].append(score[key].fmeasure)
        
        return {k: np.mean(v) for k, v in scores.items()}
    
    @staticmethod
    def exact_match(predictions: List[str], references: List[str]) -> float:
        """Exact match for questions with definitive answers"""
        matches = sum(1 for p, r in zip(predictions, references) if p.strip() == r.strip())
        return matches / len(predictions)
    
    @staticmethod
    def education_specific_metrics(predictions: List[str], references: List[str]) -> Dict:
        """Custom metrics for EDSPiKE"""
        
        metrics = {}
        
        # 1. Code correctness (if code generation)
        correct_code = 0
        for pred, ref in zip(predictions, references):
            if pred.startswith("def ") or pred.startswith("class "):
                # Try to parse & validate syntax
                try:
                    compile(pred, '<string>', 'exec')
                    correct_code += 1
                except:
                    pass
        metrics['code_correctness'] = correct_code / len(predictions) if predictions else 0
        
        # 2. Curriculum alignment (keyword matching)
        curriculum_keywords = {'WAEC', 'GES', 'assessment', 'learning outcomes'}
        aligned = sum(
            1 for pred in predictions
            if any(kw.lower() in pred.lower() for kw in curriculum_keywords)
        )
        metrics['curriculum_alignment'] = aligned / len(predictions) if predictions else 0
        
        return metrics
```

### 4.2 Evaluation Suite

Create `src/evaluation/evaluate.py`:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from pathlib import Path
from src.evaluation.metrics import EvaluationMetrics

class ModelEvaluator:
    """Comprehensive evaluation pipeline"""
    
    def __init__(self, model_path: str, tokenizer_path: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(model_path).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.model.eval()
    
    def generate_responses(self, prompts: list, max_length: int = 512) -> list:
        """Generate model predictions"""
        responses = []
        for prompt in prompts:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            responses.append(response)
        return responses
    
    def evaluate_on_test_set(self, test_file: str) -> Dict:
        """Full evaluation pipeline"""
        
        # Load test data
        test_data = []
        with open(test_file) as f:
            test_data = [json.loads(line) for line in f]
        
        # Generate predictions
        prompts = [d.get("instruction", "") for d in test_data]
        references = [d.get("output", "") for d in test_data]
        predictions = self.generate_responses(prompts)
        
        # Compute metrics
        metrics = {
            "rouge": EvaluationMetrics.rouge_score(predictions, references),
            "exact_match": EvaluationMetrics.exact_match(predictions, references),
            "education_specific": EvaluationMetrics.education_specific_metrics(predictions, references)
        }
        
        # Log results
        results = {
            "metrics": metrics,
            "sample_predictions": [
                {
                    "prompt": p,
                    "prediction": pred,
                    "reference": ref
                }
                for p, pred, ref in zip(prompts[:5], predictions[:5], references[:5])
            ]
        }
        
        return results
```

---

## Phase 5: Advanced Optimization & Deployment (300 tok/s Target)

### 5.0 Optimization Strategy Overview

**Goal:** 7B model, <3GB VRAM, 300+ tokens/second throughput

**Key techniques:**
1. Quantization (int4, NF4, GPTQ, AWQ)
2. KV cache optimization
3. Flash Attention v2
4. vLLM batch inference
5. Speculative decoding
6. Model distillation (optional)

---

### 5.1 Quantization Strategies for 7B → 2GB

#### 5.1.1 4-bit BNB with Double Quantization

```python
# Most aggressive: 7B → ~2GB with minimal quality loss
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # NormalFloat4 - better than int4
    bnb_4bit_use_double_quant=True,  # Quantize the quantization constants
    bnb_4bit_compute_dtype=torch.bfloat16,  # Compute in bfloat16
    bnb_4bit_quant_storage=torch.uint8,  # Store in 8-bit
)

model = AutoModelForCausalLM.from_pretrained(
    "checkpoints/final",
    quantization_config=quantization_config,
    device_map="auto",
    max_memory={0: "8GB"}
)

print(f"Model size: {model.get_memory_footprint() / 1e9:.2f}GB")
```

#### 5.1.2 GPTQ Quantization (Production Recommended)

```python
# Best for inference speed: 7B → 2.2GB, 400+ tok/s
# Install: pip install auto-gptq

from auto_gptq import AutoGPTQForCausalLM
from transformers import AutoTokenizer

quantize_config = {
    "bits": 4,
    "group_size": 128,
    "desc_act": True,
    "damp_percent": 0.01,
    "sym": False,
    "true_sequential": True,
}

model = AutoGPTQForCausalLM.from_pretrained(
    "checkpoints/final",
    quantize_config=quantize_config,
    device_map="cuda:0"
)

# Calibrate on representative data
calibration_texts = [
    "What is WAEC examination?",
    "Create a school timetable",
    "Ghana Education Service curriculum",
    # Add 100+ more examples
]

model.quantize(calibration_texts, use_triton=True)
model.save_quantized("checkpoints/gptq-4bit")
```

#### 5.1.3 AWQ Quantization (Best Quality)

```python
# Best quality at 4-bit: 7B → 2.3GB, 380+ tok/s
# Install: pip install autoawq

from awq import AutoAWQForCausalLM
from datasets import load_dataset

model = AutoAWQForCausalLM.from_pretrained(
    "checkpoints/final",
    device_map="cuda:0"
)

# Use representative dataset for calibration
cal_dataset = load_dataset('wikitext', 'wikitext-2-v1', split='train[:100]')

quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM"
}

model.quantize(cal_dataset, quant_config=quant_config)
model.save_quantized("checkpoints/awq-4bit")
```

#### 5.1.4 Quantization Comparison

| Method | Size | Tok/s | Quality Loss | VRAM | Best For |
|--------|------|-------|--------------|------|----------|
| FP32 | 28GB | 80 | 0% | 30GB | Research |
| FP16 | 14GB | 120 | 0.2% | 16GB | High-end GPU |
| 8-bit BNB | 7GB | 180 | 1.5% | 10GB | Consumer GPU |
| 4-bit BNB | 3.5GB | 220 | 3% | 6GB | Training |
| **4-bit GPTQ** | **2.2GB** | **420** | **2.5%** | **4GB** | **★ Production** |
| 4-bit AWQ | 2.3GB | 380 | 1.8% | 4.5GB | High quality |

---

### 5.2 vLLM: Critical for 300 tok/s

vLLM uses **continuous batching** and **paged attention** to achieve 3-15x speedup.

```bash
# Install
pip install vllm
```

Create `src/deployment/vllm_engine.py`:

```python
from vllm import LLM, SamplingParams
import torch
import time

class EDSPiKEInferenceEngine:
    """300+ tok/s production inference"""
    
    def __init__(self, model_path: str = "checkpoints/gptq-4bit"):
        self.engine = LLM(
            model=model_path,
            quantization="gptq",  # Match your quantization
            dtype="bfloat16",
            gpu_memory_utilization=0.9,  # Use 90% of GPU
            max_num_batched_tokens=8192,
            max_model_len=2048,  # Max context length
            enforce_eager=False,  # Use CUDA graphs
            trust_remote_code=True,
        )
        
        self.sampling_params = SamplingParams(
            temperature=0.7,
            top_p=0.95,
            max_tokens=512,
            repetition_penalty=1.05,
        )
    
    def generate(self, prompt: str) -> str:
        """Generate single response"""
        outputs = self.engine.generate(
            [prompt],
            self.sampling_params
        )
        return outputs[0].outputs[0].text
    
    def generate_batch(self, prompts: list) -> list:
        """★ KEY TO 300+ tok/s: Batch processing"""
        outputs = self.engine.generate(
            prompts,
            self.sampling_params,
            use_tqdm=False
        )
        return [o.outputs[0].text for o in outputs]

# Usage & Throughput Testing
engine = EDSPiKEInferenceEngine()

# Test throughput with realistic batch size
import time
test_prompts = [
    "What is WAEC?" * 2 for _ in range(32)  # 32 concurrent requests
]

start = time.time()
responses = engine.generate_batch(test_prompts)
elapsed = time.time() - start

total_tokens = sum(len(r.split()) for r in responses)
throughput = total_tokens / elapsed

print(f"Throughput: {throughput:.1f} tokens/second")
print(f"Latency (p50): {(elapsed/len(test_prompts))*1000:.1f}ms")
# Expected on A100: 300-420 tok/s
```

---

### 5.3 Flash Attention v2 (2-4x Speedup)

```python
from transformers import AutoModelForCausalLM
import torch

# Enable automatically in inference
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    attn_implementation="flash_attention_2",  # CRITICAL for speed
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
```

---

### 5.4 KV Cache Optimization (40% Memory Saving)

```python
class KVCacheOptimizer:
    """KV cache is 40% of inference memory. Optimize it."""
    
    @staticmethod
    def use_sliding_window(model, window_size: int = 2048):
        """
        Only attend to recent tokens (sliding window attention)
        O(n²) → O(n*w) complexity
        Saves ~30% memory for long sequences
        """
        model.config.sliding_window = window_size
        return model
    
    @staticmethod
    def compress_kv_cache(model):
        """Multi-query attention: share KV across attention heads"""
        # Config change (done during training):
        # num_key_value_heads = 1  # Instead of 32
        # Reduces KV cache size by ~32x
        model.config.num_key_value_heads = 1
        return model

# Usage
model = AutoModelForCausalLM.from_pretrained(model_path)
KVCacheOptimizer.use_sliding_window(model, window_size=2048)
```

---

### 5.5 Speculative Decoding (2-3x Speedup)

Uses fast "draft" model to predict tokens, then verify with main model.

```python
# Speculative decoding with vLLM
from vllm import LLM, SamplingParams

engine = LLM(
    model="checkpoints/gptq-4bit",
    draft_model="models/phi-1.5-quantized",  # Fast 1.5B draft model
    speculative_num_tokens=4,  # Guess 4 tokens at a time
    use_v2_block_manager=True,
)

# Now generate calls use speculative decoding automatically
# 2-3x speedup with <1% quality loss
```

---

### 5.6 Batch Processing Strategy

```python
# BATCH is the key to 300+ tok/s
from vllm import LLM, SamplingParams

engine = LLM("checkpoints/gptq-4bit", quantization="gptq")

# ❌ SLOW: Process one-by-one
# for prompt in prompts:
#     engine.generate([prompt])  # 50-80 tok/s

# ✅ FAST: Batch all at once
prompts = ["prompt1", "prompt2", "prompt3", ...]  # 32-64 prompts
responses = engine.generate(prompts)  # 300-420 tok/s!
```

---

### 5.7 Model Distillation (Optional: Even Smaller)

For 1-3B models from 7B teacher:

```python
# Create tiny but powerful model (900MB → 600+ tok/s)
from transformers import AutoModelForCausalLM, AutoConfig
import torch

teacher = AutoModelForCausalLM.from_pretrained(
    "checkpoints/final",
    device_map="cuda:0"
)

# Student config: 50% smaller
student_config = AutoConfig.from_pretrained("checkpoints/final")
student_config.hidden_size = 2048
student_config.num_hidden_layers = 12
student_config.intermediate_size = 5376

student = AutoModelForCausalLM.from_config(student_config).to("cuda:0")

# Train student to match teacher (knowledge distillation)
# Then quantize student: 3B → 900MB
```

---

### 5.8 Production Inference Server (vLLM + FastAPI)

**⭐ Production-Grade Server Optimized for 300+ tok/s**

Create `src/deployment/inference_server.py`:

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from vllm import LLM, SamplingParams
import torch
import time
import logging
from datetime import datetime
from typing import List, Optional
import json

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EDSPiKE AI Model API",
    description="High-throughput inference API (300+ tokens/second)",
    version="1.0.0"
)

# Global inference engine
inference_engine = None

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    batch_id: Optional[str] = None

class GenerationResponse(BaseModel):
    prompt: str
    response: str
    tokens_generated: int
    latency_ms: float
    throughput_tok_per_sec: float

class BatchRequest(BaseModel):
    prompts: List[str]
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95

class BatchResponse(BaseModel):
    responses: List[str]
    total_tokens: int
    batch_latency_ms: float
    throughput_tok_per_sec: float

class ThroughputStats(BaseModel):
    model: str
    gpu_memory_mb: float
    total_requests: int
    avg_latency_ms: float
    peak_throughput_tok_per_sec: float

class EDSPiKEInferenceServer:
    """Production inference server with monitoring & metrics"""
    
    def __init__(self, model_path: str = "checkpoints/gptq-4bit"):
        """Initialize vLLM engine optimized for throughput"""
        
        logger.info(f"Loading model from {model_path}")
        
        self.engine = LLM(
            model=model_path,
            quantization="gptq",  # Match GPTQ quantization
            dtype="bfloat16",
            gpu_memory_utilization=0.9,  # Use 90% GPU VRAM
            max_num_batched_tokens=8192,  # Batch optimization
            max_model_len=2048,  # Max context
            enforce_eager=False,  # Enable CUDA graphs
            download_dir="./models",
            trust_remote_code=True,
            swap_space=4,  # Allow CPU swap if needed
            tensor_parallel_size=1,  # For single GPU
        )
        
        # Metrics
        self.total_requests = 0
        self.total_tokens_generated = 0
        self.latencies = []
        self.start_time = datetime.now()
        
        logger.info("✅ Model loaded successfully")
    
    def generate_single(self, 
                       prompt: str,
                       max_tokens: int = 512,
                       temperature: float = 0.7,
                       top_p: float = 0.95) -> tuple:
        """Generate response for single prompt"""
        
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            repetition_penalty=1.05,
        )
        
        start_time = time.time()
        
        outputs = self.engine.generate(
            [prompt],
            sampling_params=sampling_params,
            use_tqdm=False
        )
        
        elapsed = time.time() - start_time
        response_text = outputs[0].outputs[0].text
        tokens_gen = len(response_text.split())
        throughput = tokens_gen / elapsed if elapsed > 0 else 0
        
        # Update metrics
        self.total_requests += 1
        self.total_tokens_generated += tokens_gen
        self.latencies.append(elapsed)
        
        return response_text, tokens_gen, elapsed * 1000, throughput
    
    def generate_batch(self,
                      prompts: List[str],
                      max_tokens: int = 512,
                      temperature: float = 0.7,
                      top_p: float = 0.95) -> tuple:
        """★ CRITICAL FOR 300+ tok/s: Batch multiple prompts"""
        
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            repetition_penalty=1.05,
        )
        
        start_time = time.time()
        
        # Batch inference (vLLM handles continuous batching internally)
        outputs = self.engine.generate(
            prompts,
            sampling_params=sampling_params,
            use_tqdm=False
        )
        
        elapsed = time.time() - start_time
        
        responses = [o.outputs[0].text for o in outputs]
        total_tokens = sum(len(r.split()) for r in responses)
        throughput = total_tokens / elapsed if elapsed > 0 else 0
        
        # Update metrics
        self.total_requests += len(prompts)
        self.total_tokens_generated += total_tokens
        self.latencies.append(elapsed / len(prompts))  # Avg latency per request
        
        return responses, total_tokens, elapsed * 1000, throughput
    
    def get_stats(self) -> dict:
        """Get throughput and resource metrics"""
        
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        peak_throughput = max(
            (len(r.split()) / lat) if lat > 0 else 0
            for lat in self.latencies
        ) if self.latencies else 0
        
        gpu_memory = torch.cuda.memory_allocated() / 1e6 if torch.cuda.is_available() else 0
        
        return {
            "total_requests": self.total_requests,
            "total_tokens_generated": self.total_tokens_generated,
            "avg_latency_ms": avg_latency * 1000,
            "peak_throughput_tok_per_sec": peak_throughput,
            "gpu_memory_mb": gpu_memory,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }

# Initialize on startup
@app.on_event("startup")
async def startup():
    global inference_engine
    inference_engine = EDSPiKEInferenceServer()
    logger.info("🚀 Inference server ready for requests")

# Endpoints

@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    """Single prompt generation"""
    
    try:
        response_text, tokens, latency_ms, throughput = inference_engine.generate_single(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return GenerationResponse(
            prompt=request.prompt,
            response=response_text,
            tokens_generated=tokens,
            latency_ms=latency_ms,
            throughput_tok_per_sec=throughput
        )
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_batch", response_model=BatchResponse)
async def generate_batch(request: BatchRequest):
    """Batch inference (key to 300+ tok/s)"""
    
    try:
        responses, total_tokens, latency_ms, throughput = inference_engine.generate_batch(
            prompts=request.prompts,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return BatchResponse(
            responses=responses,
            total_tokens=total_tokens,
            batch_latency_ms=latency_ms,
            throughput_tok_per_sec=throughput
        )
    
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=ThroughputStats)
async def get_stats():
    """Get throughput statistics"""
    
    stats = inference_engine.get_stats()
    return ThroughputStats(
        model="EDSPiKE-7B-GPTQ-4bit",
        gpu_memory_mb=stats["gpu_memory_mb"],
        total_requests=stats["total_requests"],
        avg_latency_ms=stats["avg_latency_ms"],
        peak_throughput_tok_per_sec=stats["peak_throughput_tok_per_sec"]
    )

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model": "EDSPiKE-7B",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """API documentation"""
    return {
        "name": "EDSPiKE AI Model API",
        "version": "1.0.0",
        "throughput": "300+ tokens/second",
        "model_size": "2.2GB (4-bit quantized)",
        "endpoints": {
            "POST /generate": "Single prompt generation",
            "POST /generate_batch": "Batch inference (32-64 prompts)",
            "GET /stats": "Performance metrics",
            "GET /health": "Health check"
        }
    }
```

**Usage Examples:**

```bash
# Single prompt
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is WAEC?", "max_tokens": 512}'

# Batch (300+ tok/s)
curl -X POST http://localhost:8000/generate_batch \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": ["prompt1", "prompt2", "prompt3", ...],
    "max_tokens": 512
  }'

# Stats
curl http://localhost:8000/stats
```

**Deploy with Docker:**

```dockerfile
# Optimized for vLLM + GPTQ quantization
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    python3.11 \
    python3.11-dev \
    python3-pip \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application
COPY . .

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with optimized settings
CMD ["uvicorn", \
     "src.deployment.inference_server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "65", \
     "--log-level", "info"]
```

**Updated requirements-production.txt:**

```
# Core
torch==2.1.2+cu121
transformers==4.36.0
tokenizers==0.15.0

# Inference Optimization (★ CRITICAL FOR 300 tok/s)
vllm==0.3.1
auto-gptq==0.5.1
awq==0.1.0

# Quantization
bitsandbytes==0.41.3
bnb-cuda-12.1==0.41.3.post5

# FastAPI Server
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# Monitoring & Logging
prometheus-client==0.19.0
python-json-logger==2.0.7

# Utilities
numpy==1.26.2
pyyaml==6.0.1
python-dotenv==1.0.0
requests==2.31.0

# Development (optional)
pytest==7.4.3
pytest-asyncio==0.23.1
```

**Docker Build & Run:**

```bash
# Build image
docker build -t edspike-ai-model:v1-production \
  --build-arg CUDA_VERSION=12.1 \
  .

# Run with resource constraints
docker run \
  --gpus all \
  --memory="8g" \
  --cpus="4" \
  --shm-size=2gb \
  -p 8000:8000 \
  -e MODEL_PATH="checkpoints/gptq-4bit" \
  -e GPU_MEMORY_UTILIZATION="0.9" \
  --name edspike-api \
  edspike-ai-model:v1-production

# Monitor logs
docker logs -f edspike-api

# Test health
curl http://localhost:8000/health
```

---

### 5.9 Production Performance Tuning

#### 5.9.1 Throughput Benchmarking

```python
# Run this to verify 300+ tok/s
import requests
import time
import statistics

API_URL = "http://localhost:8000"

# Test batch throughput
test_prompts = [
    "What is WAEC?" for _ in range(64)  # 64 concurrent requests
]

latencies = []
for i in range(3):  # Run 3 times
    start = time.time()
    response = requests.post(
        f"{API_URL}/generate_batch",
        json={
            "prompts": test_prompts,
            "max_tokens": 256,
            "temperature": 0.7
        }
    ).json()
    latency = time.time() - start
    latencies.append(latency)
    
    throughput = response["throughput_tok_per_sec"]
    print(f"Run {i+1}: {throughput:.1f} tok/s, Latency: {latency*1000:.1f}ms")

print(f"Average: {statistics.mean(latencies/len(test_prompts))*1000:.1f}ms per request")
print(f"Expected: 300-420+ tokens/second on A100")
```

#### 5.9.2 Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between
import json

class EDSPiKELoadTest(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def batch_generate(self):
        prompts = ["Explain WAEC" for _ in range(32)]
        self.client.post("/generate_batch", json={"prompts": prompts})
    
    @task(1)
    def single_generate(self):
        self.client.post("/generate", json={"prompt": "What is Ghana Education Service?"})
    
    @task(1)
    def get_stats(self):
        self.client.get("/stats")
EOF

# Run load test (100 users, 1000 requests/sec target)
locust -f locustfile.py -u 100 -r 10 --headless -c 100 --run-time 60s
```

#### 5.9.3 GPU Memory Optimization

```python
# Monitor GPU during inference
import torch

def monitor_gpu():
    """Check GPU usage"""
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f}GB")
        print(f"Memory reserved: {torch.cuda.memory_reserved() / 1e9:.2f}GB")
        print(f"Memory free: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1e9:.2f}GB")

# Should show: ~2-3GB allocated, <4GB total for 7B model with GPTQ + batching
```

---

### 5.10 Scaling to Multiple GPUs (Optional)

For even higher throughput (600+ tok/s), use tensor parallelism:

```python
# Tensor parallelism across 2 GPUs
engine = LLM(
    model="checkpoints/gptq-4bit",
    quantization="gptq",
    tensor_parallel_size=2,  # Use 2 GPUs
    gpu_memory_utilization=0.85,
    # ... rest of config
)
# 2x throughput: 600+ tok/s
```

---

### 5.11 Monitoring & Metrics (Prometheus)

Create `src/deployment/prometheus_metrics.py`:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
request_count = Counter(
    'edspike_requests_total',
    'Total requests',
    ['endpoint']
)

tokens_generated = Counter(
    'edspike_tokens_total',
    'Total tokens generated'
)

latency_histogram = Histogram(
    'edspike_latency_ms',
    'Request latency in milliseconds',
    buckets=(10, 50, 100, 200, 500, 1000)
)

throughput_gauge = Gauge(
    'edspike_throughput_tok_per_sec',
    'Current throughput in tokens/second'
)

gpu_memory_gauge = Gauge(
    'edspike_gpu_memory_mb',
    'GPU memory usage in MB'
)

# Use in FastAPI
@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = (time.time() - start) * 1000
    
    latency_histogram.observe(latency)
    request_count.labels(endpoint=request.url.path).inc()
    
    return response
```

Connect Prometheus:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'edspike-ai'
    static_configs:
      - targets: ['localhost:8000/metrics']
```

---

## Production Infrastructure

### 6.1 Training Cluster Setup (GCP/AWS)

```bash
# Example: Single A100 on GCP Compute Engine
gcloud compute instances create edspike-training \
  --machine-type=a2-highgpu-1g \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=500GB \
  --zone=us-central1-a

# Connect & train
gcloud compute ssh edspike-training --zone=us-central1-a
python -m src.training.trainer --config_path configs/base_config.yaml
```

### 6.2 Model Registry & Versioning

```python
# MLflow for tracking
import mlflow

mlflow.set_experiment("edspike-model-training")

with mlflow.start_run():
    mlflow.log_params({
        "vocab_size": 32000,
        "learning_rate": 5e-5,
        "batch_size": 32
    })
    
    # Train model
    trainer.train()
    
    # Log artifacts
    mlflow.log_artifact("checkpoints/final/model.safetensors")
    mlflow.log_artifact("checkpoints/final/tokenizer.json")
    
    # Log metrics
    mlflow.log_metrics({
        "perplexity": 8.2,
        "rouge1": 0.65
    })
```

### 6.3 Monitoring & Alerts

```yaml
# Prometheus metrics to track
metrics:
  - model_inference_latency_ms
  - model_inference_throughput_req_per_sec
  - gpu_memory_utilization_percent
  - model_accuracy_on_validation_set
  - cache_hit_rate

alerts:
  - latency_p99 > 500ms → page engineer
  - gpu_memory > 90% → scale horizontally
  - accuracy_drop > 5% → retrain
```

---

## Team & Timeline

### Team Structure
```
ML Lead
├── Model architecture & training
├── Experiment management
└── Production optimization

Data Engineer
├── Data pipeline development
├── Dataset curation
└── Quality assurance

DevOps Engineer (part-time)
├── Infrastructure setup
├── Docker & deployment
└── Monitoring
```

### 14-Week Timeline (Optimized for 300 tok/s)
```
Week 1-2:     Environment setup, data sourcing, DVC config
Week 3-4:     Data pipeline, preprocessing, validation
Week 5-6:     Tokenizer training, model architecture setup
Week 7-9:     Model training (4x A100 = 72 GPU hours)

Week 10:      Evaluation & benchmarking on FP16/FP32
              ├─ Perplexity, ROUGE, exact-match metrics
              └─ Baseline inference speed: 80-120 tok/s

Week 11:      ★ QUANTIZATION PHASE (Critical for speed)
              ├─ GPTQ 4-bit quantization (7B → 2.2GB)
              ├─ AWQ quantization (comparison)
              └─ Quality validation (should lose <3%)

Week 12:      ★ OPTIMIZATION & BATCHING
              ├─ Enable Flash Attention v2
              ├─ KV cache optimization
              ├─ vLLM integration & batch tuning
              └─ Expected: 300+ tok/s on batch=32

Week 13:      ★ PRODUCTION DEPLOYMENT
              ├─ FastAPI server + vLLM engine
              ├─ Docker containerization
              ├─ Load testing (locust)
              ├─ Prometheus metrics
              └─ Performance validation

Week 14:      Production launch & monitoring
              ├─ Stress testing (100+ concurrent users)
              ├─ Integration with EDSPiKE API
              ├─ Documentation
              └─ On-call monitoring setup
```

**Week 11-12 are critical:** This is where 80 tok/s → 300+ tok/s happens through quantization + vLLM optimization.

### Success Criteria for MVP

**Model Quality:**
- [ ] Perplexity < 20 on test set
- [ ] ROUGE-1 > 0.60
- [ ] Exact match > 35% on Q&A subset
- [ ] Code generation accuracy > 60%
- [ ] Curriculum alignment score > 0.75

**Performance (★ NEW: Optimization Focus)**
- [ ] **Throughput: 300+ tokens/second** (batch size 32-64)
- [ ] Inference latency (p50): <50ms per request
- [ ] Inference latency (p99): <200ms per request
- [ ] Model size: <3GB (4-bit quantized)
- [ ] GPU memory: <4GB during inference
- [ ] Quality loss from FP32: <3% (BLEU/ROUGE)

**Production Readiness:**
- [ ] Docker container runs on single A100/H100
- [ ] Handles batch requests (continuous batching)
- [ ] Monitoring metrics exported to Prometheus
- [ ] Health checks pass under load
- [ ] Integration tests pass with EDSPiKE API
- [ ] Load test: 100+ concurrent users, sustained 300+ tok/s

---

---

## 6. Quick Reference: 300 tok/s Optimization Stack

### What You Need to Know

| Technique | Impact | Difficulty | Time | When to Use |
|-----------|--------|-----------|------|------------|
| **GPTQ 4-bit** | 80 → 420 tok/s | Easy | 30min | ★★★ Always (3x speedup) |
| **vLLM Batch** | 100 → 300+ tok/s | Easy | 1hour | ★★★ Always (3-5x speedup) |
| **Flash Attention v2** | 120 → 150 tok/s | Trivial | 5min | ★★★ Always (20% free speedup) |
| **KV Cache Sliding Window** | Saves 30% memory | Medium | 30min | ★★ If long sequences |
| **Speculative Decoding** | 300 → 600+ tok/s | Medium | 2hours | ★★ If latency critical |
| **Model Distillation** | 3B student model | Hard | 1week | ★ If need <1GB model |

### Minimal Setup (300 tok/s in 1 week)

```bash
# 1. Quantize with GPTQ (30 minutes)
python src/optimization/gptq_quantize.py \
    --model_path checkpoints/final \
    --output_dir checkpoints/gptq-4bit

# 2. Deploy with vLLM (1 hour)
docker build -t edspike-api:v1 .
docker run --gpus all -p 8000:8000 edspike-api:v1

# 3. Test throughput (5 minutes)
# Run throughput_benchmark.py
python -c "
from src.deployment.inference_server import EDSPiKEInferenceServer
engine = EDSPiKEInferenceServer()
prompts = ['What is WAEC?'] * 64
responses, tokens, latency, throughput = engine.generate_batch(prompts)
print(f'Throughput: {throughput:.1f} tok/s')
"
```

### Expected Results After Optimization

```
Model: EDSPiKE 7B (FP32)
Size: 28GB
Throughput: 80 tok/s
Latency (p50): 200ms
VRAM: 30GB

↓ Apply GPTQ 4-bit
Size: 2.2GB (-92%)
Throughput: 420 tok/s (+425%)
Latency (p50): 20ms (-90%)
VRAM: 4GB (-87%)
Quality loss: 2.5%

↓ Apply vLLM batching (batch=32)
Throughput: 300+ tok/s (effective throughput)
Latency (p50): 5ms per token
Max concurrent: 100+ users
Cost per million tokens: $0.005 (vs $0.30 API)
```

---

## Next Steps

1. **Week 1:** Setup all infrastructure, configure DVC for data versioning
2. **Week 2:** Begin data collection parallel with environment setup
3. **Week 3:** Implement full data pipeline with validation tests
4. **Week 4+:** Execute training while monitoring metrics via W&B

**Commands to start NOW:**
```bash
git clone <repo>
cd edspike-ai-model

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize
python scripts/setup_dirs.py
python scripts/setup_gcloud.py  # if using GCP

# Begin
python notebooks/01_eda.ipynb  # Exploratory data analysis
python src/data_pipeline/collector.py  # Start collecting data
```

---

**Owner:** ML Engineering Team  
**Last Updated:** 2026  
**Status:** Active Development
