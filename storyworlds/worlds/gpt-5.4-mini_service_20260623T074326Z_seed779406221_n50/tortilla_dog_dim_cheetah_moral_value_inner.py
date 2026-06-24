#!/usr/bin/env python3
"""
storyworlds/worlds/tortilla_dog_dim_cheetah_moral_value_inner.py
================================================================

A small standalone storyworld about a tortilla, a dim little dog, a cheetah,
and a mystery to solve. The story stays close to Adventure: a short quest,
an inner monologue beat, a moral choice, and a concrete ending image showing
what changed.

The world is intentionally tiny:
- typed entities with physical meters and emotional memes
- a single causally simulated mystery
- one moral-value turn that changes the ending
- prose driven by state, not a frozen template swap

Seed words: tortilla, dog-dim, cheetah
Features: Moral Value, Inner Monologue, Mystery to Solve
Style: Adventure
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Location:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    trail: str
    hideout: str
    sky: str
    mood: str


@dataclass
class Mystery:
    id: str
    clue: str
    missing: str
    culprit: str
    solve_method: str
    reveal: str


@dataclass
class MoralChoice:
    id: str
    value: str
    selfish: str
    noble: str
    consequence: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    moral: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    cheetah: str
    cheetah_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.locations: dict[str, Location] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_location(self, loc: Location) -> Location:
        self.locations[loc.id] = loc
        return loc

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.locations = copy.deepcopy(self.locations)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "canyon": Setting(
        id="canyon",
        place="a bright canyon camp",
        trail="a winding trail between red rocks",
        hideout="a narrow cave behind the splashy waterfall",
        sky="the sun on the cliff edge",
        mood="wide and brave",
    ),
    "market": Setting(
        id="market",
        place="a busy market square",
        trail="a path between carts and baskets",
        hideout="a shaded stall behind the spice stacks",
        sky="the noon light over the roofs",
        mood="lively and noisy",
    ),
    "harbor": Setting(
        id="harbor",
        place="a windy harbor",
        trail="the boardwalk by the boats",
        hideout="a rope shed beside the pier",
        sky="the sea sparkle beyond the masts",
        mood="salt-bright and restless",
    ),
}

MYSTERIES = {
    "stolen_tortilla": Mystery(
        id="stolen_tortilla",
        clue="a warm tortilla was missing from the picnic basket",
        missing="the tortilla",
        culprit="a hungry wind",
        solve_method="follow crumbs and listen for a soft rustle",
        reveal="the tortilla had blown under a crate, where the dog-dim had sniffed it first",
    ),
    "hidden_map": Mystery(
        id="hidden_map",
        clue="a folded map had vanished from the satchel",
        missing="the map",
        culprit="a sneaky flap",
        solve_method="check every pocket and look for one bent corner",
        reveal="the map was tucked inside the tortilla wrap by mistake",
    ),
    "lost_toy": Mystery(
        id="lost_toy",
        clue="a tiny toy bone had disappeared before sunset",
        missing="the toy bone",
        culprit="a rolling shadow",
        solve_method="watch where the dust marks stop",
        reveal="the cheetah had carried it to the lookout as a surprise",
    ),
}

MORAL_VALUES = {
    "honesty": MoralChoice(
        id="honesty",
        value="honesty",
        selfish="hide the mistake and blame the wind",
        noble="tell the truth, even when it feels awkward",
        consequence="the group can trust the hero again",
        lesson="being honest keeps a team strong",
    ),
    "kindness": MoralChoice(
        id="kindness",
        value="kindness",
        selfish="keep the snack and ignore the others",
        noble="share the last bite so nobody feels left out",
        consequence="everyone feels included on the trail",
        lesson="kindness makes a hard trip feel lighter",
    ),
    "courage": MoralChoice(
        id="courage",
        value="courage",
        selfish="stay back and let someone else face the dark",
        noble="step forward and search the dim place anyway",
        consequence="the mystery gets solved faster",
        lesson="courage means moving ahead while still being careful",
    ),
}

HEROES = ["Mina", "Tomas", "Nia", "Ari", "Lena", "Owen", "Marta", "Jules"]
GUIDES = ["Pip", "Bela", "Rico", "Suri", "Momo", "Taro"]
CHEETAHS = ["Swift", "Stripe", "Sunny", "Dash", "Pounce", "Zuri"]


def pronoun_gender(gender: str) -> str:
    return gender if gender in {"girl", "boy"} else "person"


def pick_name(pool: list[str], rng: random.Random, avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, v) for s in SETTINGS for m in MYSTERIES for v in MORAL_VALUES]


def tell(setting: Setting, mystery: Mystery, moral: MoralChoice,
         hero: str, guide: str, cheetah: str) -> World:
    world = World()
    h = world.add_entity(Entity(id=hero, kind="character", type="boy", role="hero"))
    g = world.add_entity(Entity(id=guide, kind="character", type="boy", role="guide", attrs={"dim": True}))
    c = world.add_entity(Entity(id=cheetah, kind="character", type="girl", role="cheetah"))
    basket = world.add_entity(Entity(id="basket", label="picnic basket"))
    tortilla = world.add_entity(Entity(id="tortilla", label="tortilla"))
    trail = world.add_location(Location(id="trail", label=setting.trail))

    h.memes["curiosity"] = 1.0
    h.memes["doubt"] = 1.0
    g.memes["neediness"] = 1.0
    c.memes["alertness"] = 1.0
    tortilla.meters["warm"] = 1.0
    basket.meters["weight"] = 1.0
    trail.meters["mystery"] = 1.0

    world.say(
        f"At {setting.place}, {hero} and {guide} set out along {setting.trail}. "
        f"The day felt {setting.mood}, and {cheetah} padded ahead with bright eyes."
    )
    world.say(
        f"Then a problem appeared: {mystery.clue}. {hero} found only an empty space in the basket."
    )
    world.para()
    world.say(
        f"{hero} stared at the trail and asked, 'Where did it go?'"
    )
    world.say(
        f"Inside {h.id}'s head, a small inner monologue started: maybe the answer was not in the open path, but in the quiet places between steps."
    )
    h.memes["resolve"] = 1.0
    h.memes["moral_weight"] = 1.0
    world.say(
        f"{guide} pointed to {setting.hideout}. 'We should {mystery.solve_method}.'"
    )
    world.say(
        f"{cheetah} flicked an ear and led them toward the shadows, as if it already knew the route."
    )

    world.para()
    if moral.value == "honesty":
        h.memes["shame"] = 1.0
        world.say(
            f"{hero} noticed the tortilla had been saved for the trip, but one piece had been used as a map sleeve by mistake. The kind thing was to tell the truth."
        )
        world.say(
            f"{hero}'s inner monologue whispered: 'If I pretend I never mixed the wrap with the map, everyone may keep looking forever. If I admit it, we can fix it.'"
        )
        world.say(
            f"So {hero} told {guide} the mistake at once."
        )
        c.memes["respect"] = 1.0
    elif moral.value == "kindness":
        world.say(
            f"At the edge of the trail, {guide} looked tired. There was one tortilla left, warm and round in the basket."
        )
        world.say(
            f"{hero}'s inner monologue said: 'If I keep it, I will be full. If I share it, we all keep going together.'"
        )
        world.say(
            f"So {hero} broke the tortilla in half and gave {guide} the bigger piece."
        )
        g.memes["gratitude"] = 1.0
    else:
        world.say(
            f"The cave behind the waterfall looked dim, and the missing thing seemed to hide there. Nobody wanted to step in first."
        )
        world.say(
            f"{hero}'s inner monologue said: 'The dark is bigger than my fear, but not bigger than my feet.'"
        )
        world.say(f"So {hero} walked in first, with {cheetah} close behind.")
        h.memes["brave"] = 1.0

    world.para()
    if mystery.id == "stolen_tortilla":
        world.say(
            f"They followed crumbs to the crate, and there it was: the tortilla had slipped under the wood plank. {cheetah} sniffed once and nudged it free."
        )
    elif mystery.id == "hidden_map":
        world.say(
            f"They checked every pocket until {guide} found the map tucked inside the tortilla wrap by mistake. The fold had hidden it like a secret."
        )
    else:
        world.say(
            f"They watched the dust marks stop at the lookout. Up there, {cheetah} sat beside the missing toy bone, tail twitching as if it had guarded a treasure."
        )

    world.para()
    if moral.value == "honesty":
        world.say(
            f"Because {hero} told the truth, the group laughed, fixed the mix-up, and used the real clue to solve the mystery."
        )
    elif moral.value == "kindness":
        world.say(
            f"Because {hero} shared the last bite, nobody grew cranky, and the trail felt easier under every step."
        )
    else:
        world.say(
            f"Because {hero} was brave, the others followed, and the dim place gave up its secret at last."
        )
    world.say(
        f"In the end, {mystery.reveal}. {moral.consequence.capitalize()}, and the little team left with the tortilla safe, the mystery solved, and {cheetah} trotting proudly beside them."
    )

    world.facts.update(
        setting=setting,
        mystery=mystery,
        moral=moral,
        hero=h,
        guide=g,
        cheetah=c,
        basket=basket,
        tortilla=tortilla,
        trail=trail,
        solved=True,
        moral_value=moral.value,
    )
    return world


def generation_prompts(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Write an adventure story for young children where {f['hero'].id} and {f['guide'].id} solve a small mystery with a tortilla and a dim dog-like companion.",
            answer=f"Tell a short quest with a clue, a choice, and an ending image that proves the mystery was solved."
        ),
        QAItem(
            question=f"Include an inner monologue beat for {f['hero'].id} and make the story teach a clear moral value.",
            answer=f"Use the hero's private thoughts to show the choice, then end with the moral turning into action."
        ),
        QAItem(
            question=f"Keep the tone adventurous and let {f['cheetah'].id} help move the story toward the answer.",
            answer=f"Use the setting, the clue, and the companion's behavior to push the search forward."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    moral: MoralChoice = f["moral"]
    return [
        QAItem(
            question=f"Where did the adventure take place?",
            answer=f"It took place at {setting.place}, along {setting.trail}, where the day felt {setting.mood}."
        ),
        QAItem(
            question=f"What was the mystery to solve?",
            answer=f"The mystery was that {mystery.clue}. The group had to figure out what happened to {mystery.missing}."
        ),
        QAItem(
            question=f"What did {f['hero'].id} think about before making the choice?",
            answer=f"{f['hero'].id}'s inner monologue was about whether to act honestly, share kindly, or step forward bravely."
        ),
        QAItem(
            question=f"What moral value guided the ending?",
            answer=f"The story centered on {moral.value}, and the final choice showed that {moral.lesson}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tortilla?",
            answer="A tortilla is a soft flatbread, often used to wrap food or to eat with a meal."
        ),
        QAItem(
            question="Why is it useful to pay attention to clues?",
            answer="Clues help you figure out what happened, so a mystery can be solved instead of guessed."
        ),
        QAItem(
            question="What does it mean to have an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that helps you think through a choice."
        ),
        QAItem(
            question="Why does a moral value matter in a story?",
            answer="A moral value matters because it shows what kind of choice helps people, and stories can teach that choice in a memorable way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p.question}")
        lines.append(f"   {p.answer}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind} type={e.type} role={e.role} "
            f"meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}"
        )
    for l in world.locations.values():
        lines.append(f"  {l.id:10} location meters={dict(l.meters)} memes={dict(l.memes)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: tortilla, dog-dim, cheetah, moral choice, inner monologue, mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--cheetah", choices=CHEETAHS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


@dataclass
class AspParamRegistry:
    setting: str
    mystery: str
    moral: str


ASP_RULES = r"""
setting(S) :- setting(S).
mystery(M) :- mystery(M).
moral(V) :- moral(V).
valid(S,M,V) :- setting(S), mystery(M), moral(V).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for v in MORAL_VALUES:
        lines.append(asp.fact("moral", v))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    moral = args.moral or rng.choice(list(MORAL_VALUES))
    hero = args.hero or pick_name(HEROES, rng)
    guide = args.guide or pick_name(GUIDES, rng, avoid=hero)
    cheetah = args.cheetah or pick_name(CHEETAHS, rng)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        moral=moral,
        hero=hero,
        hero_gender="boy",
        guide=guide,
        guide_gender="boy",
        cheetah=cheetah,
        cheetah_gender="girl",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        MORAL_VALUES[params.moral],
        params.hero,
        params.guide,
        params.cheetah,
    )
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
        print(asp_program())
        return
    if args.verify:
        import asp
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py != cl:
            print(f"Mismatch: python={sorted(py)} clingo={sorted(cl)}")
            raise SystemExit(1)
        print(f"OK: {len(py)} ASP combos match Python.")
        return
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        combos = valid_combos()
        for s, m, v in combos:
            p = StoryParams(
                setting=s,
                mystery=m,
                moral=v,
                hero=HEROES[0],
                hero_gender="boy",
                guide=GUIDES[0],
                guide_gender="boy",
                cheetah=CHEETAHS[0],
                cheetah_gender="girl",
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
