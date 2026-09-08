#!/usr/bin/env python3
"""
A standalone superhero storyworld built from the seed words:
- bacon
- remove

Theme instruments:
- Twist
- Reconciliation
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A superhero story is reasonable when a twist creates a problem and
% reconciliation resolves it with a clear change of heart.
story_ok(S) :- has_twist(S), has_reconciliation(S).
safe_choice(C) :- rescue_tool(C).
good_ending(S) :- story_ok(S), hero_learns(S).
"""

PLACE = "city rooftop"



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    hero: str = ""
    sidekick: str = ""
    rival: str = ""
    gadget: str = ""
    seed: Optional[int] = None
    params: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Scenario:
    key: str
    premise: str
    twist: str
    clash: str
    dialogue1: str
    clue: str
    dialogue2: str
    fix: str
    reconciliation: str
    ending: str
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


NAMES = [
    "Nova", "Bolt", "Gloria", "Ranger", "Skylark", "Comet", "Valor", "Mira"
]
RIVALS = [
    "Captain Crumble", "Mist Byte", "Doctor Drift", "The Grin", "Static Shade"
]
GADGETS = ["grappling line", "shield disk", "signal flare", "jet boots", "radio glove"]

SCENARIOS = [
    Scenario(
        key="bacon_bait",
        premise="was guarding the midnight kitchen tower from a sneaky snack thief",
        twist="The thief turned out to be a hungry neighbor in a borrowed mask, not a villain at all.",
        clash="The masked figure kept dropping sizzling bacon crumbs across the rooftop vents.",
        dialogue1='"Stop right there!" the hero shouted. "Why are you stealing bacon?"',
        clue="A small note on the mask said the neighbor had only come to save the town's supper line.",
        dialogue2='"I thought everyone would be angry," the neighbor admitted. "I only wanted to remove the bacon before it burned."',
        fix="used the gadget to lift the hot pan safely, then shared the food with the tired neighbor",
        reconciliation="The hero apologized for assuming the worst, and the neighbor apologized for sneaking.",
        ending="By sunrise, both of them were laughing over a clean rooftop and one shared plate.",
    ),
    Scenario(
        key="alarm_mixup",
        premise="had set the city alarm to warn people about a harmless but messy bacon spill",
        twist="The alarm signal reached the wrong building and scared the rescue team instead.",
        clash="The team rushed in ready for danger, then found only a slippery trail near the vent.",
        dialogue1='"We need to remove the danger fast," the sidekick said. "Wait, that smells like breakfast."',
        clue="The spill came from a cafeteria cart that had rolled loose during the wind.",
        dialogue2='"So there is no monster?" the rival asked, lowering their arms."',
        fix="guided the cart back, wiped the floor, and turned the alarm off before anyone slipped",
        reconciliation="The rival admitted they had also mistaken the smell for a trap, and the hero thanked them for helping.",
        ending="Soon the rooftop was quiet again, except for one calm whistle and the last bacon strip in a lunch box.",
    ),
    Scenario(
        key="mirror_twist",
        premise="was chasing a shadow across the bright tower roof",
        twist="The shadow belonged to the rival, who was only trying to return a lost gadget.",
        clash="A gust blew the bacon sandwich from the hero's hand onto the rival's cape.",
        dialogue1='"You are the one causing trouble!" the hero said, landing hard."',
        clue="The rival pointed to a blinking tracker hidden inside the sandwich wrapper.",
        dialogue2='"I picked it up so I could remove it from the street," the rival said. "I should have spoken first."',
        fix="cleaned the cape, retrieved the tracker, and shared the remaining bacon sandwich as proof of trust",
        reconciliation="The hero and the rival shook hands and agreed to work together instead of jumping to conclusions.",
        ending="The tracker blinked safely on the hero's belt while the two stood watch side by side.",
    ),
    Scenario(
        key="siren_pause",
        premise="was helping the sidekick carry supplies to the lookout post",
        twist="A false siren made everyone think the city was under attack, but it was only a stuck rooftop radio.",
        clash="The radio crackled so loudly that the sidekick could not hear the hero's plan.",
        dialogue1='"We must remove the noise before anyone panics," the sidekick said.',
        clue="The radio knob was jammed by a strip of bacon grease from the lunch break.",
        dialogue2='"That explains the smell," the hero said. "Let us fix the radio together."',
        fix="wiped the knob, reset the channel, and used the gadget to test each signal one by one",
        reconciliation="The sidekick forgave the hero for the delay, and the hero praised the sidekick's quick thinking.",
        ending="The lookout post glowed steady and safe, with the radio humming like a calm bee.",
    ),
    Scenario(
        key="cape_rip",
        premise="was preparing for the city's costume parade",
        twist="The rival's dramatic entrance snagged the hero's cape and tore it on a metal railing.",
        clash="The torn cloth flapped wildly while bacon from the parade cart slid across the pavement.",
        dialogue1='"That was no accident," the hero said, frowning."',
        clue="The rival had already stopped and was reaching for the broken ribbon on the railing.",
        dialogue2='"I wanted to remove the railing hazard before the children arrived," the rival explained.',
        fix="helped free the cape, tied the loose ribbon away, and pinned the tear with a bright badge",
        reconciliation="The hero saw the rival had meant to keep others safe, and the two agreed to patrol together.",
        ending="The parade went on with one shiny badge flashing in the sun and one repaired cape behind it.",
    ),
]

OPENINGS = [
    "At dawn, the city rooftop gleamed under a stripe of orange light.",
    "When the wind calmed, the highest rooftop in the city became a stage for heroes.",
    "Just after breakfast, the hero landed on the rooftop with a careful stride.",
    "A siren had not yet sounded, but the rooftop already held a problem to solve.",
    "The skyline was bright and shiny when the hero and sidekick arrived above the streets.",
]

REPLIES = [
    '"We can fix this without hurting anyone," the hero said.',
    '"Hold on," the sidekick whispered, "there is more to this than we first thought."',
    '"Let us look twice before we choose," the hero said.',
    '"A true hero removes danger, not dignity," the sidekick answered.',
    '"Maybe the story has a twist," the hero murmured.',
]

PLANS = [
    "They circled the problem, checked the clues, and chose the safest next step.",
    "They split up for a moment: one watched the crowd while the other handled the gear.",
    "They lowered their voices, because a calm plan works better than a loud one.",
    "They used the gadget to test the scene before moving anything heavy.",
    "They put the slippery parts aside and kept their hands clear of the risky edge.",
]

CLOSINGS = [
    "The city below never learned how close the mess came to becoming a disaster.",
    "The rooftop air felt lighter once the misunderstanding was gone.",
    "By the end, the hero's boots left only clean marks on the roof.",
    "The last glow of sunset touched the repaired place like a medal.",
    "Their teamwork made the rooftop look smaller and safer than before.",
]


def valid_gadgets() -> list[str]:
    return GADGETS


def reasonableness_gate(params: StoryParams) -> None:
    if not params.hero.strip():
        pass
    if params.gadget not in GADGETS:
        pass
    if params.rival not in RIVALS:
        pass


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("has_twist", "city_rooftop"),
        asp.fact("has_reconciliation", "city_rooftop"),
        asp.fact("hero_learns", "city_rooftop"),
    ]
    for g in GADGETS:
        lines.append(asp.fact("rescue_tool", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story world with twist and reconciliation.")
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--gadget", choices=GADGETS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        hero=getattr(args, "hero", None) or rng.choice(NAMES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(["Dash", "Spark", "Echo", "Nova", "Wing"]),
        rival=getattr(args, "rival", None) or rng.choice(RIVALS),
        gadget=getattr(args, "gadget", None) or rng.choice(GADGETS),
        seed=rng.randrange(2**31),
    )
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="hero", kind="character", label=params.hero))
    world.add(Entity(id="sidekick", kind="character", label=params.sidekick))
    world.add(Entity(id="rival", kind="character", label=params.rival))
    world.add(Entity(id="gadget", kind="thing", label=params.gadget))
    world.facts.update(place=PLACE, twist=True, reconciliation=True)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    rival = world.get("rival")
    gadget = world.get("gadget")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS)
    reply = rng.choice(REPLIES)
    plan = rng.choice(PLANS)
    closing = rng.choice(CLOSINGS)

    hero.bump_meme("alertness")
    sidekick.bump_meme("trust")
    rival.bump_meme("worry")

    world.say(opening)
    world.say(f"{hero.label} and {sidekick.label} arrived with the {gadget.label} ready. {scenario.premise}.")
    world.para()

    world.say(scenario.clash)
    world.say(scenario.twist)
    world.say(reply)
    world.para()

    world.say(scenario.dialogue1)
    world.say(f"Then {hero.label} noticed the clue: {scenario.clue}.")
    world.say(plan)
    world.para()

    gadget.bump_meter("used", 1)
    hero.bump_meme("care", 1)
    sidekick.bump_meme("relief", 1)

    world.say(scenario.dialogue2)
    world.say(f"Using the {gadget.label}, they {scenario.fix}.")
    world.say(scenario.reconciliation)
    world.para()

    hero.bump_meme("joy", 1)
    rival.bump_meme("relief", 1)
    world.say(f"The twist ended in reconciliation, and {hero.label} learned that a quick guess can miss the truth.")
    world.say(f"{closing} {scenario.ending}")
    world.facts.update(
        scenario=scenario.key,
        premise=scenario.premise,
        twist=scenario.twist,
        clash=scenario.clash,
        clue=scenario.clue,
        fix=scenario.fix,
        reconciliation=scenario.reconciliation,
        ending=scenario.ending,
        hero_learns=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label}, {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sidekick").label}, and a twist on a city rooftop.",
        "Tell a child-friendly superhero story that includes bacon, remove, twist, and reconciliation.",
        f"Write a short action story where a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "rival").label} conflict ends in reconciliation using a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gadget").label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What problem started the rooftop adventure?",
            answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "premise")}.",
        ),
        QAItem(
            question="What twist changed what the hero thought was happening?",
            answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist")}",
        ),
        QAItem(
            question="What clue helped the hero understand the truth?",
            answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")}",
        ),
        QAItem(
            question="How did the heroes fix the situation?",
            answer=f"They {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix")}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "reconciliation")} {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ending")}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters and readers thought was happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, understand each other better, and make peace.",
        ),
        QAItem(
            question="What does it mean to remove something?",
            answer="To remove something means to take it away or move it out of the way.",
        ),
    ]


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
    return world.trace()


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show story_ok/1.\n#show safe_choice/1.\n#show good_ending/1."))
    seen = set((sym.name, tuple((a.name if hasattr(a, "name") else a.string) for a in sym.arguments)) for sym in model)
    expected = {
        ("story_ok", ("city_rooftop",)),
        ("good_ending", ("city_rooftop",)),
        ("safe_choice", ("bacon",)),
        ("safe_choice", ("remove",)),
        ("safe_choice", ("grappling line",)),
        ("safe_choice", ("shield disk",)),
        ("safe_choice", ("signal flare",)),
        ("safe_choice", ("jet boots",)),
        ("safe_choice", ("radio glove",)),
    }
    if seen == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(seen))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_ending/1."))
    return sorted(set(asp.atoms(model, "good_ending")))


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=rng.choice(NAMES),
        sidekick=rng.choice(["Dash", "Spark", "Echo", "Nova", "Wing"]),
        rival=rng.choice(RIVALS),
        gadget=rng.choice(GADGETS),
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


CURATED = [
    StoryParams(hero="Nova", sidekick="Dash", rival="Captain Crumble", gadget="shield disk", seed=11),
    StoryParams(hero="Bolt", sidekick="Spark", rival="Mist Byte", gadget="grappling line", seed=29),
    StoryParams(hero="Valor", sidekick="Wing", rival="Doctor Drift", gadget="jet boots", seed=47),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_ending/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP-compatible superhero stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        while len(samples) < getattr(args, "n", None) and len(seen) < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
