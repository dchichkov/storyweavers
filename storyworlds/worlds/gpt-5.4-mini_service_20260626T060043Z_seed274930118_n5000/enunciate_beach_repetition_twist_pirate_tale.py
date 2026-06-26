#!/usr/bin/env python3
"""
storyworlds/worlds/enunciate_beach_repetition_twist_pirate_tale.py
===================================================================

A tiny pirate-tale story world set on a beach, with repetition and a twist.

Seed tale:
---
On a windy beach, a little pirate apprentice named Mina wanted to enunciate
a message to her crew. She kept trying to speak clearly over the waves, but
the wind kept swallowing her words. Her captain worried that if Mina leaned
near the surf in her good shirt, the spray and sand would soil it. Mina tried
again and again: "Enunciate, Mina, enunciate!" At last, she used a conch horn.
The words came out clear, and the twist was that the message was not for the
crew at all. It was for a shy dolphin waiting by the shore, and the dolphin
answered with a splash.

World model:
---
* typed entities with physical meters and emotional memes
* repeated attempts raise effort and frustration
* a conch horn resolves the speaking problem
* the ending image proves the change: clear speech on the beach

The story is small on purpose: one tension, one turn, one cheerful ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wet", "sandy", "dirty", "effort"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "frustration", "resolve", "love", "curiosity"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the beach"
    breeze: str = "windy"
    affords: set[str] = field(default_factory=lambda: {"enunciate", "shell_call"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = "enunciate"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.call_count = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.call_count = self.call_count
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


@dataclass
class Rule:
    name: str
    apply: callable


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sandy"] < THRESHOLD and actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in {"torso", "head"}:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("splash", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sandy"] += 1
            item.meters["dirty"] += 1
            out.append(f"The sea spray left {item.label} sandy.")
    return out


CAUSAL_RULES = [Rule("splash", _r_splash)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def reasonableness_ok(activity: Activity, prize: Prize) -> bool:
    return prize_at_risk(activity, prize) and select_gear(activity, prize) is not None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["sandy"] >= THRESHOLD}


def activity_lullaby() -> str:
    return "the waves kept answering with a hush and a hiss"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.call_count += 1
    actor.meters[activity.mess] += 1
    actor.meters["effort"] += 1
    actor.memes["resolve"] += 0.5
    actor.memes["frustration"] += 0.5
    world.say(f"{actor.id} tried to {activity.verb}, and {activity_lullaby()}.")
    if world.call_count >= 2:
        actor.memes["frustration"] += 0.5
        world.say(f"{actor.id} tried again and again: \"Enunciate,\" {actor.id} said, \"enunciate!\"")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, mate: Entity) -> None:
    world.say(f"{hero.id} was a little pirate apprentice who loved clear words and brave plans.")
    world.say(f"{hero.pronoun().capitalize()} and {mate.id} came to {world.setting.place} to practice a message.")

def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["love"] += 1
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a tiny captain on watch.")


def warning(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict(world, hero, activity, prize.id)
    if pred["soiled"]:
        parent.memes["worry"] += 1
        world.say(f"\"Mind your {prize.label},\" {parent.id} said. \"The spray will make it sandy.\"")


def twist(world: World, hero: Entity, shell: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"Then the twist came: the message was not for the crew at all.")
    world.say(f"It was for a shy dolphin near the foam, and {hero.id} held up the shell to listen.")


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["frustration"] = 0.0
    world.say(f'{parent.id} smiled and offered a answer to the windy beach: "{gear.prep}."')
    world.say(f"{hero.id} did, and the shell horn turned {hero.pronoun('possessive')} words crisp and clear.")
    world.say(f"\"Enunciate!\" {hero.id} called once more, and this time the dolphin splashed back.")
    world.say(
        f"By the end, {hero.id} was {activity.gerund} with {prize.label} staying clean, "
        f"and the beach sounded bright with waves, laughter, and one clear pirate call."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(id="shirt", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))
    shell = world.add(Entity(id="shell", type="shell", label="conch horn", phrase="a bright conch horn",
                             owner=hero.id, caretaker=parent.id, protective=True, covers={"head", "torso"}))
    shell.worn_by = hero.id
    hero.memes["love"] += 1
    world.say(f"{hero.id} loved the beach, the ropes, and the sound of pirate words.")
    setup_prize(world, hero, prize)
    world.para()
    introduce(world, hero, parent)
    warning(world, hero, parent, activity, prize)
    _do_activity(world, hero, activity)
    world.para()
    world.say(f"{hero.id} took a breath, then tried again: \"Enunciate! Enunciate!\"")
    world.say(f"The wind kept chewing the ends of the words.")
    twist(world, hero, shell)
    gear = GEAR[0]
    resolve(world, hero, parent, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, shell=shell)
    return world


SETTINGS = {
    "beach": Setting(place="the beach", breeze="windy", affords={"enunciate"}),
}

ACTIVITIES = {
    "enunciate": Activity(
        id="enunciate",
        verb="enunciate a pirate message",
        gerund="enunciating the message",
        rush="holler at the surf",
        mess="sandy",
        soil="sandy",
        zone={"torso"},
        weather="windy",
        keyword="enunciate",
        tags={"pirate", "beach", "voice", "enunciate"},
    )
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean white shirt",
        type="shirt",
        region="torso",
    )
}

GEAR = [
    Gear(
        id="shell",
        label="conch horn",
        covers={"head", "torso"},
        guards={"sandy"},
        prep="put the conch horn to your mouth and speak into it",
        tail="used the conch horn to carry the words over the waves",
    )
]

GIRL_NAMES = ["Mina", "Rae", "Lina", "Pip", "Nori"]
BOY_NAMES = ["Finn", "Jace", "Toby", "Owen", "Kip"]
TRAITS = ["brave", "curious", "cheerful", "stubborn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for p in SETTINGS for a in SETTINGS[p].affords for pr in PRIZES if reasonableness_ok(ACTIVITIES[a], PRIZES[pr])]


KNOWLEDGE = {
    "enunciate": [("What does it mean to enunciate?", "To enunciate means to speak clearly so other people can understand your words.")],
    "beach": [("What is a beach?", "A beach is a sandy place next to the sea or ocean.")],
    "pirate": [("What is a pirate?", "A pirate is a person in stories who sails on the sea and looks for adventure.")],
    "shell": [("What is a conch horn?", "A conch horn is a shell that can be held near the mouth to help make a loud sound.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for small children set on a beach and include the word "{f["activity"].keyword}".',
        f"Tell a short story where {f['hero'].id} keeps trying to enunciate a message, but the wind keeps interrupting.",
        f"Write a gentle story with repetition and a twist, ending with a conch horn and a happy splash.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Where was {hero.id} when {hero.pronoun()} tried to {activity.verb}?",
            answer=f"{hero.id} was at {world.setting.place}, where the wind was strong and the waves kept moving.",
        ),
        QAItem(
            question=f"Why did the captain worry about {hero.pronoun('possessive')} {prize.label}?",
            answer=f"The captain worried that the sea spray and sand would make {hero.pronoun('possessive')} {prize.label} sandy.",
        ),
        QAItem(
            question=f"What repeated words did {hero.id} keep saying?",
            answer=f"{hero.id} kept saying, \"Enunciate, enunciate,\" because {hero.pronoun()} wanted the message to sound clear.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The message was not really for the crew. It was for a shy dolphin near the shore.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the windy problem?",
            answer=f"{hero.id} used a conch horn, so the words could carry over the beach and the waves.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("beach")
    tags.add("pirate")
    tags.add("shell")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  calls made: {world.call_count}")
    return "\n".join(lines)


CURATED = [StoryParams(place="beach", activity="enunciate", prize="shirt", name="Mina", gender="girl", parent="captain", trait="brave")]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not reasonably risk {prize.label} here.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate beach story world with repetition and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
