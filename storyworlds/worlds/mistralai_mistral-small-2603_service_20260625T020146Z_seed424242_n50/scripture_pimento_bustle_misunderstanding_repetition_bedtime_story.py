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

# Shared constants and world model thresholds
THRESHOLD = 0.7        # small -> big enough to matter
INITIAL_CONFUSION = 0.5  # starting level if misunderstood

# Typed meters and memes used in this domain
PHYSICAL = {"pulse", "restlessness"}
EMOTIONAL = {"confusion", "joy", "trust", "wonder"}

# Logging fired rules for narration and ASP consistency
Fired = set

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    worn_by: Optional[str] = None
    region: str = "hands"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandmother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "father": "dad"}.get(self.type, self.type)

class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: Fired = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""  # evening mood only
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_confusion_speech(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["confusion"] >= THRESHOLD and "misunderstands" not in world.fired:
            world.fired.add("misunderstands")
            out.append(f"{actor.pronoun().capitalize()} piped up, {actor.pronoun('possessive')} voice rising.")
            out.append(f'"Wait, you said "pimenteau"?  Like a grand piano?" {actor.pronoun()} laughed, clapping small hands.')
            actor.memes["confusion"] += 0.3
            for other in world.characters():
                if other.id != actor.id:
                    other.memes["trust"] -= 0.2
    return out

def _r_bustle(world: World) -> list[str]:
    out: list[str] = []
    total_restlessness = sum(e.meters["restlessness"] for e in world.characters())
    if total_restlessness >= THRESHOLD and "bustle" not in world.fired:
        world.fired.add("bustle")
        out.append('The quiet room filled with a sudden "busy-ness": chairs scraped, the old clock ticked twice, and Mira\'s grandmother fussed with the steaming cup.')
        for actor in world.characters():
            actor.memes["wonder"] += 0.1
            actor.memes["trust"] -= 0.1
    return out

def _r_repetition_soothes(world: World) -> list[str]:
    out: list[str] = []
    if ("pimento" in world.facts.values()) and ("repeated" not in world.fired):
        world.fired.add("repeated")
        world.facts["repeats_left"] = 3
    if world.facts.get("repeats_left", 0) > 0 and "soothes" not in world.fired:
        world.fired.add("soothes")
        world.facts["repeats_left"] -= 1
        out.append('Grandma smiled warmly and said again, "pimento milk, the kind that helps dreams dance."')
        out.append(f'{Mira.it().capitalize()} sighed happily, {Mira.pronoun("possessive")} eyelids drooping a little.')
        Mira = world.get("Mira")
        Mira.memes["trust"] += 0.3
        Mira.memes["wonder"] += 0.2
        Mira.meters["pulse"] -= 0.4
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="confusion_speech", tag="social", apply=_r_confusion_speech),
    Rule(name="bustle", tag="physical", apply=_r_bustle),
    Rule(name="repetition_soothes", tag="narrative", apply=_r_repetition_soothes),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def Mira rests() -> str:
    return {
        "restless": "picked at the coverlet, dreaming of adventures",
        "quiet": "snuggled deep into the pillow, eyes half-shut",
    }.get("quiet")

def Grandma prepares offering() -> str:
    return "set out a small pottery cup filled with golden milk"

def evening detail(setting: str) -> str:
    mood = {"bedroom": "golden lamplight cast long shadows",
            "temple": "flickering oil lamps dappled the stone floor",
            "veranda": "cicadas hummed the night lullaby"}.get(setting, "the evening air smelled of woodsmoke")
    return f"{mood.capitalize()}, perfect for a story."

def Mira hears(phrase: str) -> str:
    return f'"{phrase}" {Mira.pronoun().capitalize()} echoed back, flipping the sounds in {Mira.pronoun("possessive")} mind.'

def bustle activity() -> str:
    return 'cups clinked and chairs shuffled as everyone hunted for a grand piano in a house without one'

def resolve misunderstanding(target: str, phrase: str) -> str:
    return (f'{Grandma.pronoun("subject").capitalize()} chuckled, "The spice, little one — '
            f'pimento, for warmth and sweet dreams."  {Mira.pronoun("subject")} giggled, relief washing over {Mira.pronoun("object")}.')

def tell(setting: str, hero_name: str = "Mira", elder_name: str = "Grandma") -> World:
    world = World(setting)
    world.weather = ""

    Mira = world.add(Entity(
        id=hero_name, kind="character", type="girl",
        traits=["diligent", "imaginative", "small"],
        label="Mira", phrase="a girl with plaited hair",
    ))
    Grandma = world.add(Entity(
        id=elder_name, kind="character", type="grandmother",
        label="Grandma", phrase="Grandma with her apron pockets full of stories",
    ))
    Milk = world.add(Entity(
        id="pimento_milk", kind="object", type="drink",
        label="pimento milk", phrase="steaming cup of pimento-spiced milk",
        plural=False,
    ))

    world.say(f"{Mira.pronoun().capitalize()} knelt on the woven mat, {Mira.rests()}.")
    world.say(f"Outside {world.setting}, {evening detail(setting)}.")
    world.para()
    world.say(f"{Grandma.label_word} {Grandma.id} {Grandma prepares offering()}.")
    world.say('"Tonight," {Grandma.pronoun().capitalize()} whispered, "you finish your glass of pimento milk then we read the evening scripture."')
    world.facts["phrase_spoken"] = "pimento milk"

    world.para()
    Mira.memes["confusion"] = INITIAL_CONFUSION
    world.say(Mira hears("pimento-milk"))
    propagate(world)

    world.para()
    if Mira.memes["confusion"] >= THRESHOLD:
        world.say(f'{Mira.id} jumped up, {Mira.pronoun("object")} eyes wide. "A Gwand piano?"')
        world.facts["misunderstanding"] = "piano vs pimento"
        propagate(world)
        world.say(bustle activity())
        for c in world.characters():
            c.meters["restlessness"] += 0.9
        propagate(world)

    world.para()
    world.say(resolve misunderstanding("pimento", "pimento milk"))
    for i in range(3):
        world.facts["repeats_left"] = 2 - i
        world.say('Grandma smiled warmly and said again, "pimento milk, the kind that helps dreams dance."')
        Propagation clears tension
        Mira.memes["trust"] += 0.3
        Mira.meters["pulse"] -= 0.3

    world.para()
    world.say('{Mira.pronoun().capitalize()} snuggled under the quilt, the last drops of milk chased by gentle scripture on flourishing stars.')
    world.facts.update(hero=Mira, elder=Grandma, prize=Milk, setting=setting,
                       phrase_spoken=world.facts["phrase_spoken"],
                       misunderstanding=world.facts.get("misunderstanding"))
    return world

# Registries --------------------------------------------------------------
SETTINGS = {
    "bedroom": "bedroom",
    "temple": "temple nook",
    "veranda": "veranda corner",
}

PRIZES = {
    "milk": "small cup of warm milk",
}

LILAC_NAMES = ["Mira", "Lila", "Nina", "Tara", "Chira"]

@dataclass
class StoryParams:
    setting: str
    name: str
    elder: str = "Grandma"
    seed: Optional[int] = None

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a warm short bedtime tale for 3-to-5-year-olds where a child hears "pimento milk" as "piano milk", '
        f'causing gentle confusion until a loving elder repeats the word {len([k for k in f if "repeat" in k])} times '
        'for soothing dreams.',
        f'Build a cozy scene around the bedtime phrase "pimento milk" said by an {f["elder"]}. '
        'Conclude with the child feeling safe and happy, ruhama."',
        'Create a gentle story including the noun "pimento" and a repeated calming phrase ending with '
        f'comfort in {hero.it()}.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder = f["hero"], f["elder"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    qa: list[QAItem] = [
        QAItem(
            question=f'Who is the main character waiting for {elder} in the {world.setting}?',
            answer=f'It is {hero.id}, a {hero.traits[0]} {hero.type} with plaited hair, who is almost asleep.',
        ),
        QAItem(
            question=f'What drink did {elder} prepare using the word "pimento"?',
            answer=f'{elder} made {pos} a warm cup of pimento-spiced milk to help {obj} sleep.',
        ),
        QAItem(
            question=f'Why did {hero.id} jump up when {elder} said "pimento milk"?',
            answer=f'{hero.id} misheard "pimento" as "piano" and thought {elder} offered to play music '
                   f'instead of serving a drink — causing a tiny bustle of furniture shifts while everyone looked for a piano.',
        ),
    ]
    if world.facts.get("misunderstanding"):
        qa.append(QAItem(
            question=f'How did {elder} clear up the small confusion for {hero.id} at bedtime?',
            answer=resolve misunderstanding("pimento", "pimento milk"),
        ))
    if "repeats_left" in world.facts:
        qa.append(QAItem(
            question=f'How many times did Grandma repeat the phrase to calm {hero.id}?',
            answer=f'Grandma repeated the phrase "{world.facts.get("phrase_spoken")}" three times so '
                   f'{hero.id} felt safe and {hero.it()} slipped into sleep.',
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is pimento?",
                answer="Pimento is a warm spice from the dried berry of an evergreen tree. "
                      "It tastes sweet-savory, like a hug in flavor."),
        QAItem(question="Why do grown-ups repeat soothing phrases at bedtime?",
                answer="Repeating gentle phrases helps a child calm down by anchoring them to familiar words, "
                      "making the world feel safe and predictable."),
        QAItem(question="What does scripture mean at bedtime?",
                answer="Bedtime scripture is a short, peaceful story from a holy book told to bring comfort "
                      "and good dreams before a child sleeps under the covers."),
    ]

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
    lines.append("== (3) World knowledge questions (no story needed) ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ASP twin ------------------------------------------------------------------
ASP_RULES = r"""
% Misunderstanding arises when the spoken phrase and the heard phrase differ
misunderstands(P) :- heard(Piano), said(pimento).
heard(piano) :- said(Spoken), contains_lower(Spoken, "piano").
said("pimento milk").
said("pimento").

% Repetition calms the child
repeats(N) :- repeats_once, N=1.
repeats(N) :- repeats(N1), N=N1+1, N<4.
calms :- repeats(3).

% The warm bedtime resolution requires three repeats
resolved :- calms, understands(pimento).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("said", "pimento milk"))
    lines.append(asp.fact("steaming"))
    lines.append(asp.fact("quilt"))
    lines.append(asp.fact("evening"))
    lines.append(asp.fact("scripture"))
    lines.append(asp.fact("child", "Mira"))
    lines.append(asp.fact("elder", "Grandma"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show resolved/0.")), "resolved"))
    wants = clingo_set != set()
    if wants:
        print("OK: clingo confirms bedtime tale resolves with repetition and understanding.")
        return 0
    print("MISMATCH: story resolution not found in ASP.")
    return 1

# Standard storyworld interface -----------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Small bedtime world: scripture, pimento, and gentle repetitions.")
    ap.add_argument("--setting", choices=SETTINGS, default="bedroom")
    ap.add_argument("--name", choices=LILAC_NAMES)
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
    setting = args.setting or "bedroom"
    name = args.name or rng.choice(LILAC_NAMES)
    return StoryParams(setting=setting, name=name, seed=args.seed)

def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool=False, qa: bool=False, header: str="") -> None:
    if header: print(header)
    print(sample.story)
    if trace and sample.world: print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def dump_trace(world: World) -> str:
    lines = ["--- world state ---"]
    for e in world.entities.values():
        b = []
        if any(v for v in e.meters.values()): b.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()): b.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} {e.type:12} {' '.join(b)}")
    lines.append(f"  fired steps: {sorted(set(n for n,_ in world.fired))}")
    return "\n".join(lines)

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolves/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        m = asp.one_model(asp_program("#show resolves/0."))
        print("ASP confirms the bedtime tale resolves with scripture and pimento." if m else
              "ASP found no resolution.")
        return

    base_seed = args.seed or random.randrange(2**31)
    samples: list[StorySample] = []
    seen = set()
    i = 0
    while len(samples) < args.n and i < max(args.n*50, 50):
        seed = base_seed + i
        i += 1
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError as err:
            print(err); return
        sample = generate(params)
        key = sample.story
        if key in seen: continue
        seen.add(key)
        samples.append(sample)

    if args.json:
        if len(samples)==1: print(samples[0].to_json())
        else: print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i,s in enumerate(samples):
        header = f"### {s.params.name}'s pimento bedtime in the {s.params.setting}" if args.all or args.n>1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1: print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
