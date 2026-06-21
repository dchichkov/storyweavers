#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/platform_impulse_gouda_flashback_inner_monologue_dialogue.py
==============================================================================================

A tiny superhero storyworld about a kid hero, a train platform, an impulsive
mistake, and a gouda cheese snack that unlocks a flashback, an inner monologue,
and dialogue with a sidekick and a mentor.

The world simulates:
- a hero with a strong impulse meter and a courage meme,
- a platform scene where a choice happens,
- a flashback that explains a lesson,
- a dialogue-driven turning point,
- and a final image proving the hero changed.

This script follows the Storyweavers world contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily in ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
IMPULSE_HOT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"impulse": 0.0, "risk": 0.0, "cheese": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"courage": 0.0, "worry": 0.0, "focus": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    safe_spot: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Prompt:
    id: str
    urge: str
    danger: str
    lesson: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    smell: str
    tag: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Response:
    id: str
    sense: int
    effect: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    setting: str
    prompt: str
    item: str
    response: str
    hero_name: str
    hero_gender: str
    mentor_name: str
    mentor_gender: str
    sidekick_name: str
    sidekick_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "metro": Setting("metro", "the city metro platform", "The platform hummed under the bright signboards and the echoing rails.", "the bench by the wall"),
    "museum": Setting("museum", "the rooftop platform of the sky-tram", "The platform floated over the glowing museum lights.", "the safe room"),
    "harbor": Setting("harbor", "the ferry platform", "The platform smelled of salt and engines, with gulls circling above.", "the waiting shelter"),
}

PROMPTS = {
    "sneeze": Prompt("sneeze", "wanted to dash after a dropped cape", "the tracks below were dangerous", "pause before leaping"),
    "signal": Prompt("signal", "wanted to grab a blinking signal switch", "the wrong switch could stop the platform", "ask first"),
    "rescue": Prompt("rescue", "wanted to rush out for a dramatic rescue", "the hero was not ready yet", "listen to a teammate"),
}

ITEMS = {
    "gouda": Item("gouda", "gouda", "a wedge of gouda", "nutty"),
    "sandwich": Item("sandwich", "sandwich", "a cheese sandwich", "buttery"),
    "cracker": Item("cracker", "cracker", "a stack of crackers", "crisp"),
}

RESPONSES = {
    "pause": Response("pause", 3, 3, "stopped, took a breath, and checked the danger again", "kept going, but the danger was bigger than the plan", "stopped, took a breath, and checked the danger again", {"calm"}),
    "ask": Response("ask", 3, 2, "turned to the mentor and asked for a better plan", "asked too late, after the moment had already slipped away", "turned to the mentor and asked for a better plan", {"dialogue"}),
    "share": Response("share", 2, 2, "offered the gouda and let the team think together", "shared a snack, but it did not fix the danger", "offered the gouda and let the team think together", {"gouda"}),
}

HEROES = ["Nova", "Milo", "Zuri", "Tess", "Aria", "Jett"]
MENTORS = ["Captain Lantern", "Sparkline", "Aunt Comet", "Doctor Echo"]
SIDEKICKS = ["Bolt", "Pip", "Radar", "Glint"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROMPTS:
            for i in ITEMS:
                if i == "gouda":
                    combos.append((s, p, i))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def reasonableness_check(prompt: Prompt, item: Item) -> bool:
    return item.id == "gouda" and prompt.id in PROMPTS


def _flashback(world: World, hero: Entity, mentor: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["focus"] += 1
    world.say(
        f'For a blink, {hero.id} remembered the day {mentor.id} had said, '
        f'"A hero can feel an impulse and still choose."'
    )
    world.say(
        f"In that flashback, {hero.id} had seen {mentor.id} stop at a platform edge, '
        f'look both ways, and wait for the safe green light."
    )


def _dialogue(world: World, hero: Entity, mentor: Entity, sidekick: Entity, item: Item, prompt: Prompt) -> None:
    world.say(f'"{hero.id}!" called {sidekick.id}. "What are you doing?"')
    world.say(f'"I had an impulse," {hero.id} admitted. "{prompt.urge.capitalize()}."')
    world.say(f'"Then use your brain-suit," {mentor.id} said. "What does the safe hero do?"')
    world.say(f'{hero.id} looked at the {item.label}. "Maybe share the {item.label} first," {hero.pronoun()} said.')
    world.say(f'"That is a better plan," said {sidekick.id}.')


def _danger_tick(world: World, hero: Entity) -> None:
    hero.meters["impulse"] += 1
    hero.meters["risk"] += 1
    hero.memes["worry"] += 1


def tell(setting: Setting, prompt: Prompt, item: Item, response: Response,
         hero_name: str, hero_gender: str, mentor_name: str, mentor_gender: str,
         sidekick_name: str, sidekick_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    snack = world.add(Entity(id="snack", type="thing", label=item.label))
    hero.meters["impulse"] = 2.0
    hero.memes["courage"] = 1.0
    world.say(
        f"{hero.id} stood on {setting.place}, where {setting.detail.lower()} "
        f"{prompt.urge}."
    )
    world.say(
        f"In {hero.pronoun('possessive')} pocket was {item.phrase}, and the smell was so "
        f"{item.smell} that it made the choice feel extra tempting."
    )
    _flashback(world, hero, mentor)
    world.para()
    world.say(f"{hero.id} felt the {prompt.lesson} inside {hero.pronoun('possessive')} chest.")
    _danger_tick(world, hero)
    _dialogue(world, hero, mentor, sidekick, item, prompt)
    if response.sense >= 3:
        world.para()
        body = response.text.replace("{item}", item.label)
        world.say(f"At last, {hero.id} {body}.")
        hero.meters["impulse"] = 0.0
        hero.memes["focus"] += 2
        hero.memes["worry"] = 0.0
        world.say(
            f"The platform stayed safe, and the little wedge of gouda ended up shared "
            f"between three smiling heroes under the bright station lights."
        )
    else:
        world.para()
        body = response.fail.replace("{item}", item.label)
        world.say(f"{hero.id} {body}.")
        world.say(
            f"The moment wobble-bounced into a mess, but {mentor.id} reached in, steadied "
            f"{hero.pronoun('object')}, and helped everyone step back from the edge."
        )
    world.facts.update(hero=hero, mentor=mentor, sidekick=sidekick, snack=snack, prompt=prompt, item=item, response=response, outcome="safe")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prompt = f["prompt"]
    item = f["item"]
    return [
        f'Write a superhero story for a 4-to-6-year-old where {hero.id} has an impulse on a platform and remembers a helpful flashback.',
        f'Tell a short story that includes the words "platform", "{item.label}", and "impulse", with dialogue that helps the hero make a safer choice.',
        f'Write a superhero story where a mentor, a sidekick, and {hero.id} talk through a tempting moment and end with everyone safe.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    prompt = f["prompt"]
    item = f["item"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, a young superhero who had to handle a sudden impulse on a platform. {mentor.id} and the sidekick helped {hero.id} choose a safer path."),
        ("Why did the flashback matter?",
         f"It reminded {hero.id} of a lesson about pausing before acting. That memory gave {hero.id} enough focus to listen instead of rushing."),
        ("What did the dialogue change?",
         f"The talking gave {hero.id} time to think aloud and share the problem. Once the hero said the plan out loud, the safer choice became easy to see."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a platform?",
         "A platform is a flat place where people stand or wait. In a station, it is the place next to the tracks or vehicles."),
        ("What is impulse?",
         "An impulse is a quick feeling that makes you want to act right away. Heroes still need to pause and think before following it."),
        ("What is gouda?",
         "Gouda is a kind of cheese. It is soft enough to slice and can be shared as a snack."),
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="metro", prompt="sneeze", item="gouda", response="pause", hero_name="Nova", hero_gender="girl", mentor_name="Captain Lantern", mentor_gender="man", sidekick_name="Bolt", sidekick_gender="boy"),
    StoryParams(setting="museum", prompt="signal", item="gouda", response="ask", hero_name="Milo", hero_gender="boy", mentor_name="Sparkline", mentor_gender="woman", sidekick_name="Pip", sidekick_gender="girl"),
    StoryParams(setting="harbor", prompt="rescue", item="gouda", response="share", hero_name="Zuri", hero_gender="girl", mentor_name="Doctor Echo", mentor_gender="man", sidekick_name="Glint", sidekick_gender="boy"),
]


def explain_rejection(prompt: Prompt, item: Item) -> str:
    return f"(No story: this world only uses the gouda snack as the tempting item, and the chosen prompt must be one of the approved superhero platform moments.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: platform, impulse, gouda, flashback, inner monologue, dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prompt", choices=PROMPTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
    if args.prompt and args.item and not reasonableness_check(PROMPTS[args.prompt], ITEMS[args.item]):
        raise StoryError(explain_rejection(PROMPTS[args.prompt], ITEMS[args.item]))
    setting = args.setting or rng.choice(list(SETTINGS))
    prompt = args.prompt or rng.choice(list(PROMPTS))
    item = args.item or "gouda"
    response = args.response or rng.choice(list(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HEROES)
    mentor_name = args.mentor_name or rng.choice(MENTORS)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICKS)
    return StoryParams(
        setting=setting,
        prompt=prompt,
        item=item,
        response=response,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mentor_name=mentor_name,
        mentor_gender=mentor_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key in ("setting", "prompt", "item", "response"):
        if getattr(params, key) not in globals()[key.upper() + "S"]:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting],
        PROMPTS[params.prompt],
        ITEMS[params.item],
        RESPONSES[params.response],
        params.hero_name,
        params.hero_gender,
        params.mentor_name,
        params.mentor_gender,
        params.sidekick_name,
        params.sidekick_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROMPTS:
        lines.append(asp.fact("prompt", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
        if i == "gouda":
            lines.append(asp.fact("tempting", i))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, I) :- setting(S), prompt(P), item(I), tempting(I).
safe(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show safe/1."))
    return sorted(x for (x,) in asp.atoms(model, "safe"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    else:
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
