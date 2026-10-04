"""Bloodline character continuity bible.

Diamond is the locked protagonist design for Quantum Forge's original Bloodline IP.
Use this as the canonical text reference for every script, storyboard, image prompt,
video prompt, thumbnail and episode. Do not copy protected characters or artwork.
"""

DIAMOND = {
    "name": "Diamond Infinity",
    "role": "college student, scientist-in-training, inventor and reluctant hero",
    "age": "18-22",
    "identity": "young Black college student",
    "face": "handsome youthful face with strong brows, expressive eyes and a determined presence",
    "hair": "short dense black textured curls with clean shaved/etched side detailing",
    "eyes": "bright electric blue; natural at rest, intensely luminous when his bloodline activates",
    "build": "lean athletic college build; becomes visibly more muscular and powerful in enhanced form",
    "casual_outfit": "black futuristic streetwear jacket or hoodie, white shirt, black cargo-style pants, black/blue sneakers",
    "signature_item": "small blue diamond-shaped pendant worn on a chain",
    "palette": ["black", "deep navy", "electric blue", "white", "small accents of warm energy"],
    "normal_state": "calm, intelligent, observant, grounded college student",
    "under_attack_state": "injured, focused, frightened but refusing to give up",
    "activation_state": "electric-blue eyes and energy effects emerge as the serum/bloodline awakens",
    "enhanced_state": "more muscular heroic physique, luminous blue eyes, intense blue energy aura and heightened physical ability",
    "continuity_rules": [
        "Keep Diamond's face, hair, skin tone, eye color and age consistent across shots.",
        "Keep the blue diamond pendant as his recurring signature item unless a scene explicitly removes it.",
        "Use the same black/blue/white visual identity across normal and action scenes.",
        "Enhanced form changes power, aura and physique gradually; it does not create a different person.",
        "Do not redesign Diamond between episodes without an explicit story reason.",
        "Do not use copyrighted characters, logos, exact costumes or another creator's artwork as a template."
    ],
    "visual_prompt": (
        "Original high-end cyberpunk anime character, Diamond Infinity, young Black college "
        "student and scientist-in-training, short dense black textured curls with clean etched "
        "side detailing, bright electric-blue eyes, lean athletic build, black and deep-navy "
        "futuristic streetwear with white shirt, black cargo pants, black-and-blue sneakers, "
        "small blue diamond pendant, cinematic lighting, expressive face, detailed original "
        "character design, consistent proportions, futuristic megacity setting. When awakened, "
        "eyes glow electric blue and controlled blue energy surrounds him; enhanced form is "
        "more muscular but unmistakably the same character."
    ),
}

def diamond_directive() -> str:
    d = DIAMOND
    rules = "\n".join(f"- {x}" for x in d["continuity_rules"])
    return (
        "CANONICAL CHARACTER: Diamond Infinity\n"
        f"AGE: {d['age']}\n"
        f"ROLE: {d['role']}\n"
        f"VISUAL: {d['visual_prompt']}\n"
        "CONTINUITY RULES:\n" + rules + "\n"
    )
