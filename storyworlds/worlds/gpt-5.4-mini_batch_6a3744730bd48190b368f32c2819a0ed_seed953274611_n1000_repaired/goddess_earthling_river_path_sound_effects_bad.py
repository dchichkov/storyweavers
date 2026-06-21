#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/goddess_earthling_river_path_sound_effects_bad.py
===================================================================================

A small standalone storyworld for a pirate-tale-style river path adventure:
a bold earthling follows a goddess along the waterway, sound effects build the
scene, a tempting risky choice goes wrong, and the ending turns bad. The story
is constraint-checked, state-driven, and includes rhyme.

The premise is simple:
- a goddess guides an earthling along a river path,
- they hear splashy sound effects and sing little rhymes,
- the earthling ignores a warning and reaches for a flashy shell-lantern,
- the river current takes the prize and the boat, and the ending is a loss.

This world intentionally supports a bad ending; there is no rescue branch.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    path_name: str = "river path"
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
class Charm:
    id: str
    label: str
    phrase: str
    where: str
    makes_glow: bool = False
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Rival:
    id: str
    label: str
    danger: int
    pull: int
    text: str
    fail: str
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


@dataclass
class StoryParams:
    setting: str = "river_path"
    charm: str = "shell_lantern"
    rival: str = "fast_current"
    heroine: str = "Astra"
    earthling: str = "Milo"
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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_wet_sound(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    if path.meters["wet"] < THRESHOLD:
        return out
    sig = ("wet_sound",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("goddess").memes["alert"] += 1
    world.get("earthling").memes["wonder"] += 1
    out.append("Swish! the river brushed the stones like a silver sleeve.")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    boat = world.get("boat")
    if boat.meters["lost"] < THRESHOLD:
        return out
    sig = ("loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("earthling").memes["grief"] += 1
    world.get("goddess").memes["grief"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("wet_sound", _r_wet_sound), Rule("loss", _r_loss)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_ok(setting: Setting, charm: Charm, rival: Rival) -> bool:
    return setting.id == "river_path" and charm.makes_glow and rival.pull >= rival.danger


def valid_combos() -> list[tuple[str, str, str]]:
    return [("river_path", c.id, r.id) for c in CHARM_REGISTRY.values() for r in RIVAL_REGISTRY.values() if reasonableness_ok(SETTING_REGISTRY["river_path"], c, r)]


def _simulate_loss(world: World, rival: Rival) -> None:
    boat = world.get("boat")
    path = world.get("path")
    boat.meters["lost"] += rival.pull
    path.meters["danger"] += rival.danger
    propagate(world, narrate=False)


def predict_loss(world: World, charm: Charm, rival: Rival) -> dict:
    sim = world.copy()
    _simulate_loss(sim, rival)
    return {
        "lost": sim.get("boat").meters["lost"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
    }


def sail_setup(world: World, goddess: Entity, earthling: Entity, setting: Setting) -> None:
    goddess.memes["pride"] += 1
    earthling.memes["joy"] += 1
    world.say(
        f"On the river path, {goddess.id} and {earthling.id} rode a narrow boat past reeds and glimmering mud. "
        f"{setting.detail}"
    )


def sound_effects(world: World, goddess: Entity, earthling: Entity) -> None:
    world.say(
        f"Splish! went the oars, and the water answered, Plunk-plink! as if it liked the tune."
    )
    world.say(
        f'{earthling.id} grinned. "{goddess.id}, the river sounds like a drum!" {earthling.pronoun()} said.'
    )


def rhyme(world: World, goddess: Entity, earthling: Entity) -> None:
    goddess.memes["merry"] += 1
    world.say(
        f'{goddess.id} sang, "Row by the foam, keep your heart at home; '
        f'follow the tide, and the stars will guide."'
    )
    world.say(
        f'{earthling.id} clapped along and rhymed back, "Little wave, brave wave, make the lantern behave!"'
    )


def warning(world: World, goddess: Entity, earthling: Entity, charm: Charm) -> None:
    goddess.memes["caution"] += 1
    world.say(
        f'{goddess.id} touched {earthling.pronoun("possessive")} shoulder. "Leave {charm.label_word} be. '
        f'The river path can snatch shiny things."'
    )


def defy(world: World, earthling: Entity, charm: Charm) -> None:
    earthling.memes["defiance"] += 1
    world.say(
        f'"Bah," said {earthling.id}, and reached for {charm.phrase} {charm.where}.'
    )


def sink_event(world: World, charm: Charm, rival: Rival) -> None:
    world.get("charm").meters["drift"] += 1
    world.get("boat").meters["lost"] += 1
    world.get("path").meters["danger"] += rival.danger
    propagate(world, narrate=False)
    world.say(
        f"{rival.text} rose with a roar, and the {charm.label} slipped from the boat."
    )
    world.say(
        f"Whoosh! It spun once in the brown water, then vanished beneath the reeds."
    )


def ending_loss(world: World, goddess: Entity, earthling: Entity, charm: Charm) -> None:
    goddess.memes["grief"] += 1
    earthling.memes["grief"] += 1
    world.say(
        f"The boat bumped the bank and stopped cold. {goddess.id} reached out, but the path had already won."
    )
    world.say(
        f"{earthling.id} stared at the empty hands and whispered, "
        f'"No more tricks for shiny things."'
    )
    world.say(
        f"And there on the river path, under the gray spray, the brave little rhyme went quiet."
    )


SETTING_REGISTRY = {
    "river_path": Setting(
        id="river_path",
        place="river path",
        detail="The path curled beside the water like a rope from a pirate ship.",
        path_name="river path",
    )
}

CHARM_REGISTRY = {
    "shell_lantern": Charm(
        id="shell_lantern",
        label="shell lantern",
        phrase="a shell lantern",
        where="by the stern",
        makes_glow=True,
        tags={"glow", "shiny"},
    ),
    "river_token": Charm(
        id="river_token",
        label="river token",
        phrase="a bright river token",
        where="at the edge of the seat",
        makes_glow=False,
        tags={"shiny"},
    ),
}

RIVAL_REGISTRY = {
    "fast_current": Rival(
        id="fast_current",
        label="fast current",
        danger=2,
        pull=2,
        text="The current went yank-yank and shoved against the hull",
        fail="The current laughed and tugged harder",
        tags={"water", "current"},
    ),
    "muddy_splash": Rival(
        id="muddy_splash",
        label="muddy splash",
        danger=1,
        pull=1,
        text="A muddy splash slapped the side with a SPLAT",
        fail="The splash kept slapping with a mean little slap",
        tags={"water", "mud"},
    ),
}

GODDESS_NAMES = ["Astra", "Luma", "Mira", "Selene", "Nyra"]
EARTHLING_NAMES = ["Milo", "Nico", "Rae", "Pip", "Theo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-tale story for a 3-to-5-year-old that includes the words "goddess" and "earthling".',
        f"Tell a river-path adventure where {f['goddess'].id} guides {f['earthling'].id}, there are splashy sound effects, and a rhyme appears.",
        f"Write a child-friendly bad-ending story on a river path where a shiny {f['charm'].label} is lost to the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    goddess = f["goddess"]
    earthling = f["earthling"]
    charm = f["charm"]
    qa = [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {goddess.id}, a goddess, and {earthling.id}, an earthling, traveling together on the river path.",
        ),
        QAItem(
            question="What sound effects happen in the story?",
            answer="The story uses sound effects like Splish, Plunk-plink, and Whoosh to make the river feel lively and wild.",
        ),
        QAItem(
            question="What did the earthling try to do?",
            answer=f"{earthling.id} tried to grab {charm.phrase} even after being warned to leave it alone.",
        ),
    ]
    if f.get("loss"):
        qa.append(
            QAItem(
                question="Why did the ending go badly?",
                answer=f"The ending went badly because the river current was stronger than the little boat, and the shiny {charm.label} slipped away into the water. Once that happened, the path turned from playful to sad very fast.",
            )
        )
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended with loss and quiet sadness. The boat stopped at the bank, the shiny thing was gone, and the rhyme fell silent on the wet path.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["charm"].tags) | set(f["rival"].tags) | {"river", "goddess", "earthling"}
    out = []
    if "shiny" in tags:
        out.append(QAItem("Why can shiny things distract a child?", "Shiny things can be exciting because they catch the eye and feel special. That can make a child reach for them even when it is not safe."))
    out.append(QAItem("What is a river current?", "A river current is the moving water that flows along the river. It can push boats and tug at things near the water."))
    out.append(QAItem("What is a goddess?", "A goddess is a powerful female figure from stories and myths. In a story she can guide others, speak with strength, and feel larger than ordinary life."))
    out.append(QAItem("What is an earthling?", "An earthling is a person from Earth. In a story, that can simply mean a human child or traveler."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, charm: Charm, rival: Rival, goddess_name: str, earthling_name: str) -> World:
    world = World()
    goddess = world.add(Entity(id=goddess_name, kind="character", type="goddess", role="guide", traits=["wise"]))
    earthling = world.add(Entity(id=earthling_name, kind="character", type="earthling", role="seeker", traits=["bold"]))
    path = world.add(Entity(id="path", kind="thing", type="path", label="river path"))
    boat = world.add(Entity(id="boat", kind="thing", type="boat", label="little boat"))
    charm_ent = world.add(Entity(id="charm", kind="thing", type="charm", label=charm.label))
    world.facts.update(setting=setting, charm=charm, rival=rival, goddess=goddess, earthling=earthling, path=path, boat=boat, charm_ent=charm_ent)

    sail_setup(world, goddess, earthling, setting)
    world.para()
    sound_effects(world, goddess, earthling)
    rhyme(world, goddess, earthling)
    world.para()
    warning(world, goddess, earthling, charm)
    defy(world, earthling, charm)
    world.say(f"{rival.text}!")
    sink_event(world, charm_ent, rival)
    world.para()
    ending_loss(world, goddess, earthling, charm)
    world.facts["loss"] = True
    return world


def explain_rejection() -> str:
    return "(No story: this world is built to end badly, but the chosen parts still need a river-path hazard and a glowing charm.)"


def valid_story_params(params: StoryParams) -> bool:
    return params.setting in SETTING_REGISTRY and params.charm in CHARM_REGISTRY and params.rival in RIVAL_REGISTRY


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "river_path":
        raise StoryError("(No story: this world only lives on a river path.)")
    setting = "river_path"
    charm = args.charm or rng.choice(list(CHARM_REGISTRY))
    rival = args.rival or rng.choice(list(RIVAL_REGISTRY))
    if not reasonableness_ok(SETTING_REGISTRY[setting], CHARM_REGISTRY[charm], RIVAL_REGISTRY[rival]):
        raise StoryError(explain_rejection())
    return StoryParams(setting=setting, charm=charm, rival=rival, heroine=args.heroine or rng.choice(GODDESS_NAMES), earthling=args.earthling or rng.choice(EARTHLING_NAMES))


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError("(Invalid story parameters.)")
    setting = SETTING_REGISTRY[params.setting]
    charm = CHARM_REGISTRY[params.charm]
    rival = RIVAL_REGISTRY[params.rival]
    world = tell(setting, charm, rival, params.heroine, params.earthling)
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


ASP_RULES = r"""
valid(S, C, R) :- setting(S), charm(C), rival(R), river_path(S), glowing(C), strong(R).
loss :- chosen_rival(R), pull(R, P), danger(R, D), P >= D.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTING_REGISTRY]
    lines += [asp.fact("river_path", sid) for sid in SETTING_REGISTRY]
    for cid, c in CHARM_REGISTRY.items():
        lines.append(asp.fact("charm", cid))
        if c.makes_glow:
            lines.append(asp.fact("glowing", cid))
    for rid, r in RIVAL_REGISTRY.items():
        lines.append(asp.fact("rival", rid))
        lines.append(asp.fact("pull", rid, r.pull))
        lines.append(asp.fact("danger", rid, r.danger))
        lines.append(asp.fact("strong", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    try:
        sample = generate(StoryParams())
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale river path storyworld with a goddess, an earthling, rhyme, sound effects, and a bad ending.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--charm", choices=CHARM_REGISTRY)
    ap.add_argument("--rival", choices=RIVAL_REGISTRY)
    ap.add_argument("--heroine")
    ap.add_argument("--earthling")
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


CURATED = [
    StoryParams(setting="river_path", charm="shell_lantern", rival="fast_current", heroine="Astra", earthling="Milo"),
    StoryParams(setting="river_path", charm="shell_lantern", rival="muddy_splash", heroine="Luma", earthling="Rae"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
