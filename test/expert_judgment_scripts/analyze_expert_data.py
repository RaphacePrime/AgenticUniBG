"""
Expert Judgment Evaluation - Data Analysis Script
Analyzes expert evaluation data from the R1_Evaluation.xlsx file.

3 Experts evaluated 20 questions (1-20, corresponding to risposte1.txt)
along 3 quality dimensions:
  - Clarity & Completeness
  - Context Deviation  
  - Score (overall)
Each rated on a 5-point Likert scale.
"""

import openpyxl
import numpy as np
import json
import re
import os
from collections import Counter

# ============================================================
# 1. LOAD DATA
# ============================================================

XLSX_PATH = os.path.join(os.path.dirname(__file__), '..', 'experts_evaluation', 'R1_Evaluation.xlsx')
wb = openpyxl.load_workbook(XLSX_PATH)

DIMENSIONS = ['Clarity & Completeness', 'Context Deviation', 'Score']
DIM_ROWS = {
    'Clarity & Completeness': 5,
    'Context Deviation': 6,
    'Score': 7,
}

EXPERT_SHEETS = ['Expert 1', 'Expert 2', 'Expert 3']

def parse_rating(cell_value):
    """Extract numeric rating from string like '(5) Excellent'"""
    if cell_value is None:
        return None
    m = re.match(r'\((\d)\)', str(cell_value))
    if m:
        return int(m.group(1))
    return None

# Load all data into a structured dict
# data[expert_idx][dimension][question_idx] = rating (1-5)
data = {}
for ei, sheet_name in enumerate(EXPERT_SHEETS):
    ws = wb[sheet_name]
    data[ei] = {}
    for dim_name, row_num in DIM_ROWS.items():
        data[ei][dim_name] = {}
        for col_idx in range(2, 22):  # columns B(2) to U(21) = questions 1-20
            q_num = col_idx - 1  # question number 1-20
            cell = ws.cell(row=row_num, column=col_idx)
            rating = parse_rating(cell.value)
            if rating is not None:
                data[ei][dim_name][q_num] = rating

# Determine which questions have data (from all experts)
all_questions = set()
for ei in data:
    for dim in data[ei]:
        all_questions.update(data[ei][dim].keys())
all_questions = sorted(all_questions)

print(f"Total questions with data: {len(all_questions)}")
print(f"Number of experts: {len(EXPERT_SHEETS)}")
print(f"Quality dimensions: {DIMENSIONS}")

# ============================================================
# 2. FLATTEN ALL RATINGS
# ============================================================

all_ratings = []
all_ratings_by_dim = {d: [] for d in DIMENSIONS}
all_ratings_by_question = {q: [] for q in all_questions}
all_ratings_by_expert = {ei: [] for ei in range(3)}

for ei in range(3):
    for dim in DIMENSIONS:
        for q in all_questions:
            if q in data[ei][dim]:
                r = data[ei][dim][q]
                all_ratings.append(r)
                all_ratings_by_dim[dim].append(r)
                all_ratings_by_question[q].append(r)
                all_ratings_by_expert[ei].append(r)

total_assessments = len(all_ratings)
print(f"\nTotal individual assessments: {total_assessments}")
print(f"  (= {len(EXPERT_SHEETS)} experts × {len(DIMENSIONS)} dimensions × {len(all_questions)} questions)")

# ============================================================
# 3. OVERALL QUALITY ASSESSMENT
# ============================================================

print("\n" + "="*60)
print("OVERALL QUALITY ASSESSMENT")
print("="*60)

overall_mean = np.mean(all_ratings)
overall_sd = np.std(all_ratings, ddof=1)
print(f"Overall Mean: {overall_mean:.2f} ± {overall_sd:.2f}")
print(f"Total assessments: {total_assessments}")

rating_counts = Counter(all_ratings)
print("\nRating Distribution:")
for r in [5, 4, 3, 2, 1]:
    count = rating_counts.get(r, 0)
    pct = count / total_assessments * 100
    labels = {5: "Excellent", 4: "Good", 3: "Average", 2: "Below Average", 1: "Poor"}
    print(f"  Rating {r} ({labels[r]}): {pct:.1f}% ({count})")

# ============================================================
# 4. BY QUALITY DIMENSION
# ============================================================

print("\n" + "="*60)
print("ASSESSMENT BY QUALITY DIMENSION")
print("="*60)

dim_stats = {}
for dim in DIMENSIONS:
    vals = all_ratings_by_dim[dim]
    mean_val = np.mean(vals)
    sd_val = np.std(vals, ddof=1)
    min_val = min(vals)
    max_val = max(vals)
    dim_stats[dim] = {'mean': mean_val, 'sd': sd_val, 'count': len(vals), 'min': min_val, 'max': max_val}
    print(f"{dim}: {mean_val:.2f} ± {sd_val:.2f} (n={len(vals)}, range=[{min_val}, {max_val}])")

# ============================================================
# 5. BY QUESTION
# ============================================================

print("\n" + "="*60)
print("ASSESSMENT BY QUESTION")
print("="*60)

question_stats = {}
for q in all_questions:
    vals = all_ratings_by_question[q]
    mean_val = np.mean(vals)
    sd_val = np.std(vals, ddof=1)
    question_stats[q] = {'mean': mean_val, 'sd': sd_val, 'count': len(vals)}
    print(f"Q{q}: {mean_val:.2f} ± {sd_val:.2f} (n={len(vals)})")

# Best/worst questions
sorted_qs = sorted(question_stats.items(), key=lambda x: x[1]['mean'], reverse=True)
print("\nTop 5 Best Questions:")
for q, s in sorted_qs[:5]:
    print(f"  Q{q}: {s['mean']:.2f} ± {s['sd']:.2f}")
print("\nTop 5 Worst Questions:")
for q, s in sorted_qs[-5:]:
    print(f"  Q{q}: {s['mean']:.2f} ± {s['sd']:.2f}")

# ============================================================
# 6. BY EXPERT
# ============================================================

print("\n" + "="*60)
print("ASSESSMENT BY EXPERT")
print("="*60)

expert_stats = {}
for ei in range(3):
    vals = all_ratings_by_expert[ei]
    mean_val = np.mean(vals)
    sd_val = np.std(vals, ddof=1)
    expert_stats[ei] = {'mean': mean_val, 'sd': sd_val, 'count': len(vals)}
    print(f"Expert {ei+1}: {mean_val:.2f} ± {sd_val:.2f} (n={len(vals)})")

# ============================================================
# 7. DIMENSION x QUESTION BREAKDOWN
# ============================================================

print("\n" + "="*60)
print("DIMENSION x QUESTION BREAKDOWN")
print("="*60)

dim_q_stats = {}
for dim in DIMENSIONS:
    dim_q_stats[dim] = {}
    for q in all_questions:
        vals = []
        for ei in range(3):
            if q in data[ei][dim]:
                vals.append(data[ei][dim][q])
        if vals:
            dim_q_stats[dim][q] = {'mean': np.mean(vals), 'sd': np.std(vals, ddof=1) if len(vals) > 1 else 0, 'values': vals}

for dim in DIMENSIONS:
    print(f"\n{dim}:")
    for q in all_questions:
        s = dim_q_stats[dim].get(q)
        if s:
            print(f"  Q{q}: {s['mean']:.2f} ± {s['sd']:.2f} (values: {s['values']})")

# ============================================================
# 8. INTER-EXPERT AGREEMENT
# ============================================================

print("\n" + "="*60)
print("INTER-EXPERT AGREEMENT")
print("="*60)

# For each scenario (question x dimension), check agreement
# A scenario = (question, dimension)
scenarios = []
for q in all_questions:
    for dim in DIMENSIONS:
        ratings = []
        for ei in range(3):
            if q in data[ei][dim]:
                ratings.append(data[ei][dim][q])
        if len(ratings) == 3:
            scenarios.append({'q': q, 'dim': dim, 'ratings': ratings})

total_scenarios = len(scenarios)
exact_agreement = sum(1 for s in scenarios if s['ratings'][0] == s['ratings'][1] == s['ratings'][2])
within_1_agreement = sum(1 for s in scenarios if max(s['ratings']) - min(s['ratings']) <= 1)

variances = [np.var(s['ratings'], ddof=0) for s in scenarios]
avg_variance = np.mean(variances)
sd_variance = np.std(variances, ddof=1)

print(f"Total scenarios: {total_scenarios}")
print(f"Exact agreement: {exact_agreement} ({exact_agreement/total_scenarios*100:.1f}%)")
print(f"Within 1 point: {within_1_agreement} ({within_1_agreement/total_scenarios*100:.1f}%)")
print(f"Average variance: {avg_variance:.3f} ± {sd_variance:.3f}")

# ============================================================
# 9. COHEN'S KAPPA (PAIRWISE, QUADRATIC WEIGHTED)
# ============================================================

def quadratic_weighted_kappa(r1, r2, min_rating=1, max_rating=5):
    """Calculate quadratic weighted Cohen's kappa."""
    cats = list(range(min_rating, max_rating + 1))
    n_cats = len(cats)
    
    # Build confusion matrix
    conf = np.zeros((n_cats, n_cats))
    for a, b in zip(r1, r2):
        conf[a - min_rating][b - min_rating] += 1
    
    n = len(r1)
    
    # Weight matrix (quadratic)
    weights = np.zeros((n_cats, n_cats))
    for i in range(n_cats):
        for j in range(n_cats):
            weights[i][j] = (i - j) ** 2 / (n_cats - 1) ** 2
    
    # Expected matrix
    row_sums = conf.sum(axis=1)
    col_sums = conf.sum(axis=0)
    expected = np.outer(row_sums, col_sums) / n
    
    # Calculate kappa
    observed_weighted = np.sum(weights * conf) / n
    expected_weighted = np.sum(weights * expected) / n
    
    if expected_weighted == 0:
        return 1.0
    
    kappa = 1 - observed_weighted / expected_weighted
    return kappa

print("\n--- Cohen's Kappa (Quadratic Weighted) ---")

# Prepare pairwise ratings - for each dimension and question, pair the experts
pairs = [(0, 1), (0, 2), (1, 2)]
pair_labels = ["Expert 1 vs Expert 2", "Expert 1 vs Expert 3", "Expert 2 vs Expert 3"]

kappas = []
for (e1, e2), label in zip(pairs, pair_labels):
    r1, r2 = [], []
    for dim in DIMENSIONS:
        for q in all_questions:
            if q in data[e1][dim] and q in data[e2][dim]:
                r1.append(data[e1][dim][q])
                r2.append(data[e2][dim][q])
    
    k = quadratic_weighted_kappa(r1, r2)
    kappas.append(k)
    print(f"  {label}: κ = {k:.3f}")

avg_kappa = np.mean(kappas)
print(f"\n  Average pairwise Cohen's kappa: {avg_kappa:.3f}")

# Interpret kappa
if avg_kappa < 0.0:
    interp = "poor agreement"
elif avg_kappa < 0.20:
    interp = "slight agreement"
elif avg_kappa < 0.40:
    interp = "fair agreement"
elif avg_kappa < 0.60:
    interp = "moderate agreement"
elif avg_kappa < 0.80:
    interp = "substantial agreement"
else:
    interp = "almost perfect agreement"
print(f"  Interpretation: {interp}")

# ============================================================
# 10. FLEISS' KAPPA
# ============================================================

def fleiss_kappa(ratings_matrix, n_categories=5):
    """
    Calculate Fleiss' kappa.
    ratings_matrix: list of lists, where each inner list contains
                    the ratings from all raters for one subject.
    """
    n_subjects = len(ratings_matrix)
    n_raters = len(ratings_matrix[0])
    
    # Build category count matrix
    cat_counts = np.zeros((n_subjects, n_categories))
    for i, ratings in enumerate(ratings_matrix):
        for r in ratings:
            cat_counts[i][r - 1] += 1
    
    # P_i for each subject
    P = np.zeros(n_subjects)
    for i in range(n_subjects):
        P[i] = (np.sum(cat_counts[i] ** 2) - n_raters) / (n_raters * (n_raters - 1))
    
    P_bar = np.mean(P)
    
    # p_j for each category
    p = np.sum(cat_counts, axis=0) / (n_subjects * n_raters)
    P_e = np.sum(p ** 2)
    
    if P_e == 1.0:
        return 1.0
    
    kappa = (P_bar - P_e) / (1 - P_e)
    return kappa

print("\n--- Fleiss' Kappa ---")

# Build ratings matrix: for each scenario, we have 3 ratings
ratings_matrix = []
for s in scenarios:
    ratings_matrix.append(s['ratings'])

fk = fleiss_kappa(ratings_matrix)
print(f"  Fleiss' kappa: {fk:.3f}")

if fk < 0.0:
    fk_interp = "poor agreement"
elif fk < 0.20:
    fk_interp = "slight agreement"
elif fk < 0.40:
    fk_interp = "fair agreement"
elif fk < 0.60:
    fk_interp = "moderate agreement"
elif fk < 0.80:
    fk_interp = "substantial agreement"
else:
    fk_interp = "almost perfect agreement"
print(f"  Interpretation: {fk_interp}")

# ============================================================
# 11. PER-DIMENSION RATING DISTRIBUTION
# ============================================================

print("\n" + "="*60)
print("PER-DIMENSION RATING DISTRIBUTION")
print("="*60)

for dim in DIMENSIONS:
    vals = all_ratings_by_dim[dim]
    counts = Counter(vals)
    total = len(vals)
    print(f"\n{dim}:")
    for r in [5, 4, 3, 2, 1]:
        c = counts.get(r, 0)
        print(f"  Rating {r}: {c/total*100:.1f}% ({c})")

# ============================================================
# 12. SAVE ALL RESULTS TO JSON
# ============================================================

results = {
    'overall': {
        'mean': round(overall_mean, 2),
        'sd': round(overall_sd, 2),
        'total_assessments': total_assessments,
        'rating_distribution': {str(r): {'count': rating_counts.get(r, 0), 'pct': round(rating_counts.get(r, 0) / total_assessments * 100, 1)} for r in [5, 4, 3, 2, 1]}
    },
    'by_dimension': {dim: {
        'mean': round(dim_stats[dim]['mean'], 2),
        'sd': round(dim_stats[dim]['sd'], 2),
        'count': dim_stats[dim]['count'],
        'range': [dim_stats[dim]['min'], dim_stats[dim]['max']],
        'distribution': {str(r): Counter(all_ratings_by_dim[dim]).get(r, 0) for r in [5, 4, 3, 2, 1]}
    } for dim in DIMENSIONS},
    'by_question': {str(q): {
        'mean': round(question_stats[q]['mean'], 2),
        'sd': round(question_stats[q]['sd'], 2),
        'count': question_stats[q]['count']
    } for q in all_questions},
    'by_expert': {f'Expert {ei+1}': {
        'mean': round(expert_stats[ei]['mean'], 2),
        'sd': round(expert_stats[ei]['sd'], 2),
        'count': expert_stats[ei]['count']
    } for ei in range(3)},
    'inter_expert_agreement': {
        'total_scenarios': total_scenarios,
        'exact_agreement': exact_agreement,
        'exact_agreement_pct': round(exact_agreement / total_scenarios * 100, 1),
        'within_1_agreement': within_1_agreement,
        'within_1_agreement_pct': round(within_1_agreement / total_scenarios * 100, 1),
        'avg_variance': round(avg_variance, 3),
        'sd_variance': round(sd_variance, 3),
        'cohens_kappa': {label: round(k, 3) for (_, _), label, k in zip(pairs, pair_labels, kappas)},
        'avg_cohens_kappa': round(avg_kappa, 3),
        'cohens_kappa_interpretation': interp,
        'fleiss_kappa': round(fk, 3),
        'fleiss_kappa_interpretation': fk_interp
    },
    'best_worst_questions': {
        'top_5': [{'question': q, 'mean': round(s['mean'], 2)} for q, s in sorted_qs[:5]],
        'bottom_5': [{'question': q, 'mean': round(s['mean'], 2)} for q, s in sorted_qs[-5:]]
    },
    'dimension_x_question': {
        dim: {str(q): {
            'mean': round(dim_q_stats[dim][q]['mean'], 2),
            'sd': round(dim_q_stats[dim][q]['sd'], 2),
            'values': dim_q_stats[dim][q]['values']
        } for q in all_questions if q in dim_q_stats[dim]}
        for dim in DIMENSIONS
    },
    'raw_data': {
        f'Expert {ei+1}': {
            dim: {str(q): data[ei][dim][q] for q in all_questions if q in data[ei][dim]}
            for dim in DIMENSIONS
        } for ei in range(3)
    }
}

OUTPUT_DIR = os.path.dirname(__file__)
with open(os.path.join(OUTPUT_DIR, 'analysis_results.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n\nResults saved to analysis_results.json")
print("Analysis complete!")
