#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities: characters and magical objects in a fairy-tale domain.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    rival: Optional[str] = None
    worn_on: Optional[str] = None   # body region for worn items
    # Physical meters (e.g., completeness, power) and emotional memes (e.g., tension, pride)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"elara", "maiden"}
        male = {"malrik", "sorcerer"}
        if self.id in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.id in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Parametrization knobs for the span-deceive-pro fairy tale.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str]

@dataclass
class Weaver:
    id: str
    trait: str
    profession: str = "master weaver"
    skill: float = 1.0            # base skill in pro craft
    focus_target: float = 0.8       # target focus level for stable weave

@dataclass
class Sorcerer:
    id: str
    ambition: float = 1.0
    trickery: float = 0.7         # innate deception skill

@dataclass
class Fox:
    id: str
    cleverness: float = 0.9         # trickster level

@dataclass
class Tapestry:
    name: str
    magic: float = 0.8
    regions: list[str] = field(default_factory=list)
    purpose: str = "timeweave"      # spans past/future

# ---------------------------------------------------------------------------
# World: entity store + narration state; propagates causal rules to fixpoint.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        # Facts captured during the tale for downstream Q&A.
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------
# Causal rules – forward-chaining deterministic updates
# ---------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_tension(world: World) -> list[str]:
    lines: list[str] = []
    for ch in world.characters():
        if ch.memes["pride"] >= THRESHOLD and ch.memes["ambition"] >= THRESHOLD:
            if ("tension", ch.id) not in world.fired:
                world.fired.add(("tension", ch.id))
                lines.append(f"{ch.pronoun('subject').capitalize()} felt the weight of {ch.pronoun('possessive')} own legend too heavy.")
        if world.paragraphs[-1]:
            # Lower focus once danger is sensed
            if ch.memes["tension"] >= THRESHOLD and ch.memes["caution"] < ch.metes["focus"]:
                delta = ch.memes["caution"] - ch.memes["focus"]
                if delta < -0.2:
                    world.fired.add(("focus_lost", ch.id))
                    lines.append(f"{ch.pronoun('subject')} lost {ch.pronoun('possessive')} rhythm.")
    return lines

def _r_completion(world: World) -> list[str]:
    lines: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["completeness"] >= THRESHOLD and ("complete", item.id) not in world.fired:
            world.fired.add(("complete", item.id))
            lines.append(f"The golden threads knitted themselves into {item.it()}, glowing with latent magic.")
    return lines

def _r_deception(world: World) -> list[str]:
    lines: list[str] = []
    fox = next((e for e in world.entities.values() if e.type == "fox"), None)
    weaver = next((e for e in world.entities.values() if e.type == "weaver"), None)
    if fox and weaver:
        if weaver.memes["trust"] < THRESHOLD and fox.memes["cleverness"] >= THRESHOLD:
            sig = ("deceived", fox.id, weaver.id)
            if sig not in world.fired:
                world.fired.add(sig)
                lines.append(f"{fox.id.capitalize()} curled {fox.pronoun('possessive')} tail and grinned.")
                lines.append(f"Behind {weaver.pronoun('possessive')} back, {fox.id} whispered secrets meant only for the ears of shadows.")
    return lines

CAUSAL_RULES: list[Rule] = [
    Rule(name="tension", tag="social", apply=_r_tension),
    Rule(name="completion", tag="conclusion", apply=_r_completion),
    Rule(name="deception", tag="conflict", apply=_r_deception),
]

def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)

# ---------------------------------------------------------------------
# Plot verbs – a coarse three-act screenplay
# ---------------------------------------------------------------------
def set_scene(world: World) -> None:
    world.say(f"Long ago, in {world.setting.place}, a {world.entities['elara'].traits[0]} weaver lived.")
    world.say(f"There, {world.entities['elara'].id}, the {world.entities['elara'].profession}, practiced pro moves — steady hands and silent threads.")

def build_passion(world: World) -> None:
    elara = world.get("elara")
    elara.memes["pride"] = 0.95
    elara.memes["focus"] = world.get("elara").meters.setdefault("focus_target", 0.8)
    world.say(f"{elara.id}, they said, would weave a tapestry that could span morn to night.")
    world.say(f"{elara.pronoun().capitalize()} dreamed of threads glowing across sky and bone.")

def sorcerer_spies(world: World) -> None:
    malrik = world.get("malrik")
    malrik.memes["ambition"] = 1.0
    malrik.memes["arrogance"] = 0.8
    world.say(f"Yet {malrik.id}, a sorcerer of grand ambition, coveted such power.")
    world.say(f"From his tower he cast an eye upon {malrik.pronoun('possessive')} prize: the span Elara dreamed to weave.")
    world.para()

def fox_enters(world: World) -> None:
    slyfox = world.get("slyfox")
    slyfox.memes["cleverness"] = 0.95
    world.say(f"Then {slyfox.id}, a fox of cunning wit, slunk into the village.")
    world.say(f"To the ears of shadows he purred promises of gold and ruin.")

def tempts_elara(world: World) -> None:
    elara = world.get("elara")
    malrik = world.get("malrik")
    slyfox = world.get("slyfox")
    if ("trust", "elara", "fox") not in world.facts:
        elara.memes["trust"] = 0.4
        world.say(f'"Find me a thread that walks the span of years," {slyfox.id} coaxed, "and I shall crown thee queen of lore."')
        world.say(f"{elara.pronoun().capitalize()} frowned, sensing trickery below the honeyed words.")
        world.facts["trust_lowered_by"] = slyfox.id

def warns_mortal(world: World) -> None:
    elara = world.get("elara")
    world.say(f"{elara.id}'s hands trembled on {elara.pronoun('possessive')} loom as last echoes of warning reached past rustling leaves.")

def elara_weaves(world: World) -> None:  # narrative pulse of the core activity
    item = world.get("timeweave")
    item.meters["completeness"] += 0.35
    item.meters["magic"] = min(1.0, item.meters["magic"] + 0.05)
    world.facts["loom_time_left"] = max(0.0, world.get("loom").meters.get("time_left", 2.1) - 0.2)
    world.say(f"{elara.id}’s shuttle flew across the frame, weaving lightness into cloth.")
    propagate(world)

def fox_deceives(world: World) -> None:
    elara = world.get("elara")
    slyfox = world.get("slyfox")
    if slyfox.memes["cleverness"] >= THRESHOLD:
        elara.memes["trust"] = max(0.0, elara.memes["trust"] - 0.4)
        slyfox.memes["confidence"] = 0.98  # cocky after success
        world.say(f'Sly {slyfox.id} side-stepped into shade, eyes glinting.')
        world.say(f'"Deceive thee? " {slyfox.id} laughed, "I merely spin tales the heart already wishes to believe."')
        world.fired.add(("deceived", slyfox.id, elara.id))

def malrik_strikes(world: World) -> None:
    malrik = world.get("malrik")
    weave = world.get("timeweave")
    elara = world.get("elara")
    if weave.meters["completeness"] >= THRESHOLD:
        malrik.memes["frustration"] += 0.6
        world.say(f'"Foolish girl," {malrik.id} crept near, fingers crackling with stolen light.')
        world.say(f'"Thy span stays me but a heartbeat — I shall carve mine across the centuries!"')
        world.facts["stolen_fragment"] = weave.meters["magic"] * 0.5
    else:
        world.say(f"{malrik.id} hovered like thunder poised to strike, yet hesitated.")

def resolution_hope(world: World) -> None:
    elara = world.get("elara")
    timeweave = world.get("timeweave")
    malrik = world.get("malrik")
    world.say(f"{elara.id} closed {elara.pronoun('possessive')} eyes and plucked one last thread free.")
    timeweave.meters["completeness"] = 1.0 - 1e-6  # almost perfect
    world.say(f"A shimmering tapestry of auroral hues unfurled, knitting past and future into one.")
    malrik.memes["ambition"] = 0.0
    malrik.memes["arrogance"] = 0.05
    world.say(f'"Thy folly gifts me eternity," {elara.id} declared solemnly to the dusk air.')
    world.say(f"{elara.pronoun().capitalize()} hung {timeweave.it()} upon the loom’s final beam — no longer a dream, but a truth that even shadows dared not unweave.")

# ---------------------------------------------------------------------
# tell() – build the whole fairy tale world in one call
# ---------------------------------------------------------------------
def tell(setting: Setting, weaver_id: str, sorcerer_id: str, fox_id: str, tapestry: str) -> World:
    world = World(setting)
    # Register core cast
    elara = world.add(Entity(
        id=weaver_id, kind="character", type="weaver", label="the weaver",
        phrase="Elara the careful", traits=["careful", "patient"], worn_on="loom",
    ))
    elara.memes.update({"pride": 0.6, "focus": 0.8, "love_work": 0.95})
    elara.meters.update({"focus_target": 0.8})
    world.add(Entity(id="loom", kind="thing", type="loom",
                  label="the gold-leaf loom",
                  meters={"time_left": 2.1, "quality": 0.95}))
    malrik = world.add(Entity(id=sorcerer_id, kind="character", type="sorcerer",
                           label="the sorcerer", phrase="Malrik of Amber Spire",
                           traits=[]))
    malrik.memes.update({"ambition": 0.7, "arrogance": 0.6})
    slyfox = world.add(Entity(id=fox_id, kind="character", type="fox",
                         label="Slyfox", phrase="a fox of shrewd tongue",
                         traits=["clever"]))
    slyfox.memes.update({"cleverness": 0.85})
    # Add prize tapestry
    tw = world.add(Entity(id=tapestry, kind="thing", type="tapestry",
                      label="the timeweave",
                      meters={"completeness": 0.01, "magic": 0.7},
                      traits=["radiant", "auroral"]))
    # Act 1 — Epoch of craft
    set_scene(world)
    build_passion(world)
    # Act 2 — The Ambush of Ambition
    sorcerer_spies(world)
    fox_enters(world)
    world.para()
    tempts_elara(world)
    warns_mortal(world)
    fox_deceives(world)
    world.para()
    # Act 3 — Loom and Luminary
    malrik_strikes(world)
    for _ in range(5):          # Rounds of weaving tension
        elara_weaves(world)
    world.para()
    resolution_hope(world)
    # Collect facts for downstream Q&A
    world.facts.update(lead_weaver=elara, antagonist=malrik, trickster=slyfox,
                      prize=tapestry, loom=world.get("loom"),
                      conflict_met=malrik.memes["frustration"] >= THRESHOLD,
                      resolution="completed")
    return world

# ---------------------------------------------------------------------
# Registries – small canonical sets ensuring valid fairy-tale variants.
# ---------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the Whispering Forest glade",
                     indoor=False, affords={"weave"}),
}

WEAVERS = {
    "elara": Weaver(id="elara", trait="patient", profession="master weaver", skill=1.1),
}

SORCERERS = {
    "malrik": Sorcerer(id="malrik", ambition=0.95, trickery=0.7),
}

FOXES = {
    "slyfox": Fox(id="slyfox", cleverness=0.9),
}

TAPESTRIES = {
    "timeweave": Tapestry(name="timeweave", regions=["past", "future"], purpose="gainetime"),
}

def valid_combos() -> list[tuple]:
    return sorted((p, w, s, f, t)
                 for p in SETTINGS
                 for w in WEAVERS
                 for s in SORCERERS
                 for f in FOXES
                 for t in TAPESTRIES)

# ---------------------------------------------------------------------
# Quality-assurance gates – reject impossible arguments early
# ---------------------------------------------------------------------
def explain_rejection(given: dict) -> str:
    reasons = []
    if given.get("fox") and given.get("sorcerer"):
        return ""
    if "weaver" not in given:
        reasons.append("Missing weaver (--weaver elara)")
    if "sorcerer" not in given:
        reasons.append("Missing sorcerer (--sorcerer malrik)")
    if not reasons:
        return ""
    return "(No story: " + " and ".join(reasons) + ".)"

# ---------------------------------------------------------------------
# Generation Q&A – three levels of readback
# ---------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    w = world.facts["lead_weaver"]
    return [
        f"Write a four-paragraph fairy tale about a patient weaver named {w.id} who tries to weave a tapestry that can span past and future, chasing pro mastery of her craft.",
        f"Tell the gentle story where {w.id} faces ambition from a sorcerer and deception from a cunning fox, resolving conflict with steady hands.",
        f'Compose a short fairy tale ending with the sentence: "Now the shadows dare not unweave the threads of time."'
    ]

def story_qa(world: World) -> list[QAItem]:
    w = world.facts["lead_weaver"]
    mal = world.facts["antagonist"]
    fox = world.facts["trickster"]
    t = world.facts["prize"]
    sub = w.pronoun("subject"); obj = w.pronoun("object"); pos = w.pronoun("possessive")
    return [
        QAItem(
            question=f"Who is the patient weaver at the heart of this tale?",
            answer=f"She is {w.id}, a {w.profession} of few words and steady rhythm who longs to weave a tapestry that spans the past and future.",
        ),
        QAItem(
            question=f"What ambition drove the malevolent sorcerer into the forest?",
            answer=f"{mal.id} coveted the power of a time-spanning tapestry, hoping to fix his grandeur across the centuries.",
        ),
        QAItem(
            question=f"How did Slyfox attempt to deceive the patient weaver?",
            answer=f'He spun tales of crowns and gold, whispering: "Find me a thread that walks the span of years," trying to lower {pos} guard.',
        ),
        QAItem(
            question=f"What act tested {pos} pride most gravely?",
            answer=f"When Malrik advanced to seize the near-finished tapestry did {w.id} reach across the loom and pluck one final glowing thread free.",
        ),
        QAItem(
            question=f"How did {w.id} ultimately resolve the threat of deceit and ambition?",
            answer=f'By weaving a tapestry that shimmered with auroral hues, {w.id} turned ambition to ash and the fox’s lies to silence, hanging the truth upon the loom’s final beam.',
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tapestry in fairy tales?",
               answer="A tapestry is a woven cloth with pictures or designs, often hung on walls; some tales say the finest hold magic across years."),
        QAItem(question="Why do foxes in stories often deceive?",
               answer="Story foxes usually act cunning — playful tricksters who spin half-truths to trip humans or heroes, longing for gold or glory."),
        QAItem(question="What does 'pro' mean in crafting?",
               answer="‘Pro’ in crafting means professional, or showing top skill and steady mastery so the work lives up to its truest name."),
        QAItem(question="What does a ‘timeweave’ span in stories?",
               answer="A timeweaving tapestry is said to knit past and future into one cloth; some dare to hang it upon a loom’s last beam and watch aeons flicker past."),
    ]

# ---------------------------------------------------------------------
# ASP helper – inline ASP rules twin for the reasonableness gate
# ---------------------------------------------------------------------
ASP_RULES = r"""
% A fairy-tale span-deceive-pro setting requires a weaver, a sorcerer with ambition, and a cunning fox.
needs_weaver(W) :- weaver(W), pro_skill(W,S), S >= 0.8.
needs_sorcerer(S) :- sorcerer(S), ambition(S,A), ttrick(S,T), T >= 0.6.
needs_fox(F) :- fox(F), cleverness(F,C), C >= 0.7.
valid_story(Place, Weaver, Sorcerer, Fox, Tapestry) :-
    setting(Place), affords(Place, weave),
    needs_weaver(Weaver), needs_sorcerer(Sorcerer), needs_fox(Fox),
    tapestry(Tapestry), magic(Tapestry,M), M >= 0.7.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        lines.append(asp.fact("affords", pid, "weave"))
    for wid, w in WEAVERS.items():
        lines.append(asp.fact("weaver", wid))
        lines.append(asp.fact("pro_skill", wid, round(w.skill, 2)))
    for sid, s in SORCERERS.items():
        lines.append(asp.fact("sorcerer", sid))
        lines.append(asp.fact("ambition", sid, round(s.ambition, 2)))
        lines.append(asp.fact("ttrick", sid, round(s.trickery, 2)))
    for fid, f in FOXES.items():
        lines.append(asp.fact("fox", fid))
        lines.append(asp.fact("cleverness", fid, round(f.cleverness, 2)))
    for tid, t in TAPESTRIES.items():
        lines.append(asp.fact("tapestry", tid))
        lines.append(asp.fact("magic", tid, round(t.magic, 2)))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def one_model(show: str = "") -> list[clingo.Symbol]:
    import asp
    models = asp.solve(asp_program(show), models=1)
    return models[0] if models else []

def asp_verify() -> int:
    import asp
    py_set = set(tuple(c) for c in valid_combos())
    cl_set = set(asp.atoms(one_model("#show valid_story/5."), "valid_story"))
    if py_set != cl_set:
        print("MISMATCH in compatible story sets.")
        if py_set - cl_set:
            print("  only in Python:", sorted(py_set - cl_set))
        if cl_set - py_set:
            print("  only in ASP:", sorted(cl_set - py_set))
        return 1
    print(f"OK: {len(py_set)} valid fairy-tale combinations verified.")
    return 0

# ---------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale world: span, deceive, pro.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--weaver", choices=WEAVERS)
    ap.add_argument("--sorcerer", choices=SORCERERS)
    ap.add_argument("--fox", choices=FOXES)
    ap.add_argument("--tapestry", choices=TAPESTRIES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.tapestry and args.weaver:
        # Minimal cross-check
        pass
    combo_l = [(p,w,s,f,t) for (p,w,s,f,t) in valid_combos()
               if (args.place is None or p == args.place)
               and (args.weaver is None or w == args.weaver)
               and (args.sorcerer is None or s == args.sorcerer)
               and (args.fox is None or f == args.fox)
               and (args.tapestry is None or t == args.tapestry)]
    if not combo_l:
        raise StoryError(explain_rejection(vars(args)))
    p, w, s, f, t = rng.choice(combo_l)
    return StoryParams(
        place=p, weaver=w, sorcerer=s, fox=f, tapestry=t,
        seed=args.seed if args.seed is not None else rng.randrange(2**31),
    )

@dataclass
class StoryParams:
    place: str
    weaver: str
    sorcerer: str
    fox: str
    tapestry: str
    seed: Optional[int] = None

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place],
                 params.weaver, params.sorcerer, params.fox,
                 params.tapestry)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            ms = {k:v for k,v in e.meters.items() if v}
            mes = {k:v for k,v in e.memes.items() if v}
            print(f"{e.id:10} {e.type:9}", end=" ")
            if ms: print("meters=" + str(dict(ms)), end=" ")
            if mes: print("memes=" + str(dict(mes)), end="")
            print()
        print("fired:", sorted({n for n,_ in sample.world.fired}))
    if qa:
        print("\n==  story Q&A ==")
        for qa_p in sample.story_qa:
            print(f"Q: {qa_p.question}\nA: {qa_p.answer}\n")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        atoms = asp.atoms(one_model("#show valid_story/5."), "valid_story")
        for a in sorted(atoms):
            print(f"{' '.join(str(x) for x in a)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31-1)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(p,w,s,f,t, s+100000) for p,w,s,f,t in valid_combos())]
    else:
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            key = sample.story
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = ""
        if args.all:
            p = s.params
            header = f"### {WEAVERS[p.weaver].profession} {p.weaver} — {SORCERERS[p.sorcerer].id}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
