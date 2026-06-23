#!/usr/bin/env python3
"""
storyworlds/worlds/solid_trumpet_copper_sound_effects_cautionary_fable.py
===========================================================================

A standalone tiny storyworld for a cautionary fable about a solid copper trumpet,
sound effects, and the lesson that loud choices can cause trouble.

Seed premise:
- A child or small animal finds a solid copper trumpet.
- The trumpet makes a comically loud sound effect.
- A cautious companion warns about the nearby risk.
- The loud choice causes a problem.
- The story ends with a safer choice and a clear lesson image.

The world uses typed entities with accumulating physical meters and emotional
memes, a small forward-chaining rule engine, a reasonableness gate, and an inline
ASP twin for parity checking.
"""

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


def _repo_dir() -> str:
    here = os.path.abspath(__file__)
    cur = os.path.dirname(here)
    while True:
        candidate = os.path.join(cur, "results.py")
        if os.path.exists(candidate):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


sys.path.insert(0, _repo_dir())
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    solid: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "hen"}
        male = {"boy", "father", "brother", "fox", "crow", "wolf", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class SoundAction:
    id: str
    verb: str
    effect: str
    onomatopoeia: str
    risk_meter: str
    risk_label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    place: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SaferChoice:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sound_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["loudness"] < THRESHOLD:
            continue
        sig = ("spread", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.entities.values():
            if ent.attrs.get("near_sound"):
                ent.memes["alarm"] += 1
        out.append("__sound__")
    return out


def _r_disturb_treasure(world: World) -> list[str]:
    out: list[str] = []
    treasure_id = world.facts.get("treasure_id")
    if not treasure_id or treasure_id not in world.entities:
        return out
    treasure = world.get(treasure_id)
    if treasure.meters["disturbance"] < THRESHOLD:
        return out
    sig = ("disturb", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for actor in world.characters():
        actor.memes["guilt"] += 1
    out.append("__disturb__")
    return out


CAUSAL_RULES = [
    Rule("sound_spread", "physical", _r_sound_spread),
    Rule("disturb_treasure", "physical", _r_disturb_treasure),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_check(setting: Setting, action: SoundAction, treasure: Treasure) -> bool:
    return action.id in setting.afford and treasure.risk == action.risk_meter


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for tid, treasure in TREASURES.items():
                if reasonableness_check(setting, action, treasure):
                    out.append((sid, aid, tid))
    return out


def predict_risk(world: World, actor: Entity, action: SoundAction, treasure_id: str) -> dict:
    sim = world.copy()
    _perform_action(sim, sim.get(actor.id), action, narrate=False)
    tr = sim.get(treasure_id)
    return {"disturbed": tr.meters["disturbance"] >= THRESHOLD, "alarm": sum(e.memes["alarm"] for e in sim.characters())}


def _perform_action(world: World, actor: Entity, action: SoundAction, narrate: bool = True) -> None:
    actor.meters["loudness"] += 1
    actor.memes["glee"] += 1
    world.facts["last_onomatopoeia"] = action.onomatopoeia
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, elder: Entity, action: SoundAction, treasure: Treasure) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} was a small {hero.type} with a bright eye for strange things.")
    world.say(f"One morning, {hero.id} found {treasure.phrase}.")
    world.say(f"It was a {treasure.label}, and it was made of solid copper.")
    world.say(f"{hero.id} loved its shiny weight and the way it looked ready for a tune.")
    elder.memes["watchful"] += 1


def warning(world: World, elder: Entity, hero: Entity, action: SoundAction, treasure: Treasure, scare: Entity) -> None:
    pred = predict_risk(world, hero, action, treasure.id)
    world.facts["predicted_alarm"] = pred["alarm"]
    world.facts["predicted_disturbed"] = pred["disturbed"]
    world.say(f'"Wait," {elder.id} said. "That {treasure.label} is solid, and it can carry far."')
    world.say(f'"If you blow {treasure.it()}, {scare.label} may startle, and the whole yard will know."')
    elder.memes["caution"] += 1


def defy(world: World, hero: Entity, action: SoundAction) -> None:
    hero.memes["defiance"] += 1
    world.say(f'But {hero.id} wanted to try the sound anyway.')
    world.say(f'{hero.id} lifted the trumpet and took a breath.')
    world.say(f'{"{0}!".format(action.onomatopoeia)}' if action.onomatopoeia else "")
    world.say(f'{hero.id} blew {action.effect}, and the air rang like a bell.')


def trouble(world: World, scare: Entity, treasure: Treasure) -> None:
    treasure.meters["disturbance"] += 1
    scare.memes["startled"] += 1
    propagate(world, narrate=False)
    world.say(f'The sound rolled across the yard and woke {scare.label}.')
    world.say(f'{scare.label.capitalize()} flapped and fussed, and the little crowd grew noisy.')


def resolve(world: World, elder: Entity, hero: Entity, safer: SaferChoice, treasure: Treasure) -> None:
    hero.memes["regret"] += 1
    hero.memes["wisdom"] += 1
    world.say(f'Then {elder.id} showed {hero.id} a safer choice: {safer.phrase}.')
    world.say(f'Its soft {safer.effect} stayed close, unlike the trumpet blast.')
    world.say(f'{hero.id} tried it, and the yard grew calm again.')
    world.say(f'In the end, the solid copper trumpet hung on the wall, and everyone could hear the lesson.')


def tell(setting: Setting, action: SoundAction, treasure: Treasure, safer: SaferChoice,
         hero_name: str = "Pip", hero_type: str = "mouse", elder_name: str = "Mara",
         elder_type: str = "hare", scare_name: str = "Brindle", scare_type: str = "goat") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["curious"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, traits=["wise"]))
    scare = world.add(Entity(id=scare_name, kind="character", type=scare_type, traits=["sleepy"]))
    world.add(Entity(id="trumpet", type="object", label="trumpet", solid=True, tags={"solid", "trumpet", "copper"}))
    tr = world.add(Entity(id=treasure.id, type="object", label=treasure.label, phrase=treasure.phrase, tags=set(treasure.tags)))
    tr.attrs["near_sound"] = True
    world.facts["treasure_id"] = tr.id
    world.facts["safer_id"] = safer.id

    intro(world, hero, elder, action, treasure)
    world.para()
    warning(world, elder, hero, action, treasure, scare)
    defy(world, hero, action)
    world.para()
    trouble(world, scare, treasure)
    world.para()
    elder.memes["love"] += 1
    resolve(world, elder, hero, safer, treasure)

    world.facts.update(hero=hero, elder=elder, scare=scare, action=action, treasure=tr, safer=safer, setting=setting)
    return world


@dataclass
class StoryParams:
    place: str
    action: str
    treasure: str
    safer: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    scare_name: str
    scare_type: str
    seed: Optional[int] = None


SETTINGS = {
    "yard": Setting(place="the yard", afford={"toot"}),
    "orchard": Setting(place="the orchard", afford={"toot"}),
    "barn": Setting(place="the barn", afford={"toot"}),
}

ACTIONS = {
    "toot": SoundAction(id="toot", verb="toot the trumpet", effect="a great copper blast", onomatopoeia="PAAAH", risk_meter="disturbance", risk_label="noise", tags={"sound", "cautionary"}),
}

TREASURES = {
    "hive": Treasure(id="hive", label="hive", phrase="a solid little beehive", place="near the plum tree", risk="disturbance", tags={"bees", "hive"}),
    "nests": Treasure(id="nests", label="nesting shelf", phrase="a nesting shelf of sleeping birds", place="under the eaves", risk="disturbance", tags={"birds", "nest"}),
    "calf": Treasure(id="calf", label="calf pen", phrase="a calf pen with a sleepy calf", place="by the fence", risk="disturbance", tags={"calf", "barn"}),
}

SAFER = {
    "hum": SaferChoice(id="hum", label="hum", phrase="a soft hum", effect="little notes", tags={"soft"}),
    "bell": SaferChoice(id="bell", label="bell", phrase="a tiny copper bell", effect="gentle ring", tags={"soft"}),
    "whistle": SaferChoice(id="whistle", label="whistle", phrase="a reed whistle", effect="bird-soft notes", tags={"soft"}),
}

GAMES = {
    "nora": ("Nora", "mouse"),
    "pip": ("Pip", "mouse"),
    "milo": ("Milo", "fox"),
    "tess": ("Tess", "hedgehog"),
    "mara": ("Mara", "hare"),
    "bram": ("Bram", "badger"),
}


CURATED = [
    StoryParams(place="yard", action="toot", treasure="hive", safer="hum", hero_name="Pip", hero_type="mouse", elder_name="Mara", elder_type="hare", scare_name="Brindle", scare_type="goat"),
    StoryParams(place="orchard", action="toot", treasure="nests", safer="bell", hero_name="Nora", hero_type="mouse", elder_name="Bram", elder_type="badger", scare_name="Lark", scare_type="bird"),
    StoryParams(place="barn", action="toot", treasure="calf", safer="whistle", hero_name="Milo", hero_type="fox", elder_name="Tess", elder_type="hedgehog", scare_name="Mabel", scare_type="calf"),
]


KNOWLEDGE = {
    "copper": [("What is copper?", "Copper is a shiny metal that can be shaped into pots, coins, and instruments.")],
    "trumpet": [("What does a trumpet do?", "A trumpet makes a loud musical sound when someone blows into it.")],
    "solid": [("What does solid mean?", "A solid thing keeps its shape and does not pour like water.")],
    "sound": [("Why can a loud sound be a problem?", "A loud sound can startle people and animals and make them rush around.")],
    "hive": [("Why should you stay gentle near a beehive?", "Bees can get upset if they are startled, and then they may buzz and sting.")],
    "birds": [("Why do birds need quiet?", "Birds can be startled by loud noises, especially when they are nesting.")],
    "barn": [("What is a barn?", "A barn is a big farm building where animals, hay, and tools are often kept.")],
    "soft": [("Why is a soft sound useful?", "A soft sound carries less and is less likely to scare anyone.")],
}

KNOWLEDGE_ORDER = ["solid", "copper", "trumpet", "sound", "hive", "birds", "barn", "soft"]


def valid_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.action in ACTIONS and params.treasure in TREASURES and params.safer in SAFER


def explain_rejection() -> str:
    return "(No story: this combination does not make a cautionary sound-fable here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about a solid copper trumpet and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--safer", choices=SAFER)
    ap.add_argument("--name")
    ap.add_argument("--type", dest="hero_type")
    ap.add_argument("--elder")
    ap.add_argument("--elder-type")
    ap.add_argument("--scare")
    ap.add_argument("--scare-type")
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError(explain_rejection())
    place, action, treasure = rng.choice(sorted(combos))
    safer = args.safer or rng.choice(sorted(SAFER))
    hero_name, hero_type = (args.name, args.hero_type) if args.name and args.hero_type else rng.choice(list(GAMES.values()))
    if not args.name:
        hero_name, hero_type = rng.choice(list(GAMES.values()))
    elder_name = args.elder or rng.choice(["Mara", "Bram", "Wren", "Tess"])
    elder_type = args.elder_type or rng.choice(["hare", "badger", "owl", "hedgehog"])
    scare_name = args.scare or rng.choice(["Brindle", "Lark", "Mabel", "Puck"])
    scare_type = args.scare_type or rng.choice(["goat", "bird", "calf", "hen"])
    return StoryParams(place=place, action=action, treasure=treasure, safer=safer, hero_name=hero_name, hero_type=hero_type, elder_name=elder_name, elder_type=elder_type, scare_name=scare_name, scare_type=scare_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    treasure = f["treasure"]
    action = f["action"]
    return [
        f'Write a short cautionary fable for a young child that includes the words "solid", "trumpet", and "copper".',
        f"Tell a story where {hero.id} wants to {action.verb} near {treasure.phrase}, but {elder.id} warns that the sound will cause trouble.",
        f"Write a fable about a shiny copper trumpet, a careful warning, and a softer choice at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, scare = f["hero"], f["elder"], f["scare"]
    treasure = f["treasure"]
    safer = f["safer"]
    action = f["action"]
    place = f["setting"].place
    qa = [
        QAItem(question=f"Who was the story about at {place}?", answer=f"It was about {hero.id}, who was curious about a solid copper trumpet, and {elder.id}, who tried to keep the sound from causing trouble. {scare.id} was nearby, so the choice mattered."),
        QAItem(question=f"What did {hero.id} want to do with the trumpet?", answer=f"{hero.id} wanted to {action.verb}. That was tempting because the trumpet looked shiny and fun, but it was not a quiet choice near {treasure.phrase}."),
        QAItem(question=f"Why did {elder.id} warn {hero.id}?", answer=f"{elder.id} warned {hero.id} because a loud trumpet blast can carry far and startle nearby animals. The warning fit the place, since {treasure.phrase} was close enough to be disturbed."),
    ]
    if f.get("predicted_disturbed"):
        qa.append(QAItem(question=f"What happened after the trumpet sound?", answer=f"The sound rolled across {place} and startled {scare.id}. The noise spread from the trumpet, so the fable turned into a cautionary lesson."))
    qa.append(QAItem(question=f"How did the story end?", answer=f"{hero.id} chose the softer {safer.phrase} after the trouble, and {place} grew calm again. The ending shows that a quieter choice can keep everyone safe and peaceful."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    for key in ("action", "treasure", "safer"):
        obj = world.facts[key]
        tags |= set(obj.tags)
    tags.add("solid")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.solid:
            bits.append("solid=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_combo(P,A,T) :- place(P), action(A), treasure(T), valid(P,A,T).
valid(P,A,T) :- afford(P,A), risk(A,R), treasure_risk(T,R).
sound_spread(H) :- loud(H), nearby(X), alarmable(X).
disturb(T) :- sound_spread(H), treasure(T), near_treasure(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("afford", sid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk", aid, action.risk_meter))
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_risk", tid, treasure.risk))
        lines.append(asp.fact("near_treasure", tid))
    lines.append(asp.fact("alarmable", "x"))
    lines.append(asp.fact("loud", "x"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = 0
    if python_set != clingo_set:
        print("MISMATCH between Python and ASP valid-combo gates.")
        print("python only:", sorted(python_set - clingo_set))
        print("asp only:", sorted(clingo_set - python_set))
        ok = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, action=None, treasure=None, safer=None, name=None, hero_type=None, elder=None, elder_type=None, scare=None, scare_type=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        ok = 1
    return ok


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError(explain_rejection())
    world = tell(SETTINGS[params.place], ACTIONS[params.action], TREASURES[params.treasure], SAFER[params.safer], hero_name=params.hero_name, hero_type=params.hero_type, elder_name=params.elder_name, elder_type=params.elder_type, scare_name=params.scare_name, scare_type=params.scare_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
