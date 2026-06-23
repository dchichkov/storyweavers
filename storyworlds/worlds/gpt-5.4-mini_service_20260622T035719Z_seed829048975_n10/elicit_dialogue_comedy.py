#!/usr/bin/env python3
"""
storyworlds/worlds/elicit_dialogue_comedy.py
============================================

A small comedy story world built from a seed that asks for the word "elicit",
with dialogue and a light, child-friendly comedic style.

Premise:
- A child wants to elicit a laugh for a school show.
- Their props are a little too earnest, and their helper keeps suggesting
  increasingly silly lines.
- The turn comes when the wrong prop creates the right joke, and the child
  learns that comedy often arrives by accident.

The world tracks:
- physical meters: paint, glitter, spill, wobble, sparkle
- emotional memes: nerves, confidence, laughter, pride, embarrassment

The prose is state-driven: each story is built from simulated facts, not from
swapped nouns in a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = json.loads(json.dumps(self.to_plain_entities()))
        clone.entities = {k: self._rehydrate_entity(v) for k, v in clone.entities.items()}
        clone.facts = json.loads(json.dumps(self.facts))
        clone.history = json.loads(json.dumps(self.history))
        clone.paragraphs = [list(p) for p in self.paragraphs]
        clone.fired = set(self.fired)
        return clone

    def to_plain_entities(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for k, e in self.entities.items():
            out[k] = {
                "id": e.id,
                "kind": e.kind,
                "type": e.type,
                "label": e.label,
                "phrase": e.phrase,
                "traits": list(e.traits),
                "role": e.role,
                "owner": e.owner,
                "caretaker": e.caretaker,
                "plural": e.plural,
                "tags": sorted(e.tags),
                "attrs": dict(e.attrs),
                "meters": dict(e.meters),
                "memes": dict(e.memes),
            }
        return out

    @staticmethod
    def _rehydrate_entity(data: dict[str, Any]) -> Entity:
        ent = Entity(
            id=data["id"],
            kind=data["kind"],
            type=data["type"],
            label=data["label"],
            phrase=data["phrase"],
            traits=list(data["traits"]),
            role=data["role"],
            owner=data["owner"],
            caretaker=data["caretaker"],
            plural=bool(data["plural"]),
            tags=set(data["tags"]),
            attrs=dict(data["attrs"]),
        )
        ent.meters.update(data["meters"])
        ent.memes.update(data["memes"])
        return ent


@dataclass
class Show:
    id: str
    place: str
    audience: str
    prop: str
    helper: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    color: str
    mess: str
    can_talk: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gag:
    id: str
    label: str
    line: str
    twist: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    show: str
    prop: str
    gag: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    audience: str
    seed: int | None = None


SHOWS = {
    "class_show": Show(id="class_show", place="the classroom stage", audience="the class", prop="prop_box", helper="helper_friend", sound="snicker", tags={"stage", "class", "laugh"}),
    "tiny_talent": Show(id="tiny_talent", place="the little gym stage", audience="the whole school", prop="prop_box", helper="helper_friend", sound="giggle", tags={"stage", "school", "laugh"}),
    "family_night": Show(id="family_night", place="the living room rug", audience="the cousins", prop="prop_box", helper="helper_friend", sound="chuckle", tags={"home", "laugh"}),
}

PROPS = {
    "banana_hat": Prop(id="banana_hat", label="banana hat", phrase="a bright banana hat", kind="hat", color="yellow", mess="slips", can_talk=False, tags={"hat", "yellow", "silly"}),
    "foam_shoes": Prop(id="foam_shoes", label="foam shoes", phrase="wobbly foam shoes", kind="shoes", color="blue", mess="wobbles", can_talk=False, tags={"shoes", "wobble"}),
    "sparkly_box": Prop(id="sparkly_box", label="sparkly box", phrase="a sparkly box", kind="box", color="silver", mess="spills", can_talk=True, tags={"sparkle", "box"}),
}

GAGS = {
    "loud_whisper": Gag(id="loud_whisper", label="loud whisper", line="I shall whisper the loudest joke in town", twist="the whisper came out like a trumpet", effect="laughs", tags={"whisper", "voice", "laugh"}),
    "serious_pie": Gag(id="serious_pie", label="serious pie", line="This pie is for thinking only", twist="the pie slid off the plate and wore the face instead", effect="laughs", tags={"pie", "splat", "laugh"}),
    "tiny_bow": Gag(id="tiny_bow", label="tiny bow", line="Behold my grand performance bow", twist="the bow was so tiny it looked like a sneeze", effect="giggles", tags={"bow", "tiny", "laugh"}),
}


GIRL_NAMES = ["Mia", "Lina", "Nora", "Pia", "Zoe", "Ivy", "Ada"]
BOY_NAMES = ["Finn", "Leo", "Max", "Owen", "Jude", "Sam", "Eli"]
HELPER_NAMES = ["Tess", "Noah", "Milo", "June", "Rae", "Ben"]
TRAITS = ["brave", "bouncy", "curious", "serious", "silly", "shy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for show_id in SHOWS:
        for prop_id, prop in PROPS.items():
            for gag_id in GAGS:
                if prop.kind == "hat" and gag_id == "serious_pie":
                    continue
                if prop.kind == "box" and gag_id == "tiny_bow":
                    continue
                combos.append((show_id, prop_id, gag_id))
    return combos


def explain_rejection(show_id: str, prop_id: str, gag_id: str) -> str:
    show = SHOWS[show_id]
    prop = PROPS[prop_id]
    gag = GAGS[gag_id]
    return f"(No story: {gag.label} does not fit {prop.label} on {show.place}; the joke would not start honestly.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about trying to elicit a laugh.")
    ap.add_argument("--show", choices=SHOWS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gag", choices=GAGS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--audience")
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
              if (args.show is None or c[0] == args.show)
              and (args.prop is None or c[1] == args.prop)
              and (args.gag is None or c[2] == args.gag)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    show_id, prop_id, gag_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero])
    audience = args.audience or SHOWS[show_id].audience
    if args.show and args.prop and args.gag:
        if (args.show, args.prop, args.gag) not in valid_combos():
            raise StoryError(explain_rejection(args.show, args.prop, args.gag))
    return StoryParams(show=show_id, prop=prop_id, gag=gag_id, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, audience=audience)


def init_world(params: StoryParams) -> World:
    world = World()
    show = SHOWS[params.show]
    prop = PROPS[params.prop]
    gag = GAGS[params.gag]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, traits=["little", "funny"], role="performer"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, traits=["quick"], role="helper"))
    stage = world.add(Entity(id="stage", kind="thing", type="stage", label=show.place, phrase=show.place))
    prop_ent = world.add(Entity(id="prop", kind="thing", type=prop.kind, label=prop.label, phrase=prop.phrase, tags=set(prop.tags)))
    prop_ent.attrs["color"] = prop.color
    prop_ent.attrs["mess"] = prop.mess
    world.facts.update(show=show, prop=prop, gag=gag, hero=hero, helper=helper, stage=stage, prop_ent=prop_ent)
    hero.memes["nerves"] = 2.0
    helper.memes["confidence"] = 1.0
    return world


def perform(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    show: Show = world.facts["show"]
    prop: Prop = world.facts["prop"]
    gag: Gag = world.facts["gag"]
    hero.memes["nerves"] += 1.0
    world.say(f"{hero.label} stood on {show.place} and tried to elicit a laugh from {show.audience}.")
    world.say(f'{helper.label} leaned over and said, "{gag.line}."')
    world.event("setup", place=show.place, audience=show.audience)
    world.para()
    if prop.kind == "box":
        world.say(f'{hero.label} held up {prop.phrase} and said, "This will be hilarious."')
    elif prop.kind == "hat":
        world.say(f'{hero.label} wore {prop.phrase} and bowed like a very determined noodle.')
    else:
        world.say(f'{hero.label} waddled in {prop.phrase} and tried not to giggle first.')
    world.say(f'The audience waited politely, which made the joke even harder to start.')
    world.para()
    if gag.id == "loud_whisper":
        prop.meters["wobble"] += 1
        hero.memes["embarrassment"] += 1
        helper.memes["laughter"] += 1
        world.say(f'{helper.label} whispered the joke, but it came out as a trumpet sound.')
        world.say(f'That made {prop.label} wobble and {hero.label} snort.')
        world.event("twist", effect="trumpet_whisper")
    elif gag.id == "serious_pie":
        prop.meters["spill"] += 1
        hero.memes["embarrassment"] += 1
        helper.memes["laughter"] += 1
        world.say(f'The pie slid off the plate, and the plate slid too, as if the table had joined the act.')
        world.say(f'{hero.label} stared at the face-shaped mess and laughed before anyone else could.')
        world.event("twist", effect="pie_slide")
    else:
        prop.meters["sparkle"] += 1
        hero.memes["confidence"] += 1
        helper.memes["laughter"] += 1
        world.say(f'{helper.label} made such a tiny bow that it looked like a sneeze.')
        world.say(f'{hero.label} lost the serious face and laughed, and then the whole room did too.')
        world.event("twist", effect="tiny_bow")
    world.para()
    hero.memes["confidence"] += 2.0
    hero.memes["pride"] += 1.0
    world.say(f"By the end, {hero.label} had learned that sometimes you do not force a joke; you elicit one by accident.")
    world.say(f'{show.audience} clapped, {helper.label} grinned, and {prop.label} became the star of the show.')
    world.event("end", laugh=True)
    world.facts["ending_laugh"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child that uses the word "elicit" and takes place on {f["show"].place}.',
        f'Tell a funny story where {f["hero"].label} tries to elicit laughter from {f["show"].audience}, but the prop and the joke do not behave as planned.',
        f'Write a dialogue-heavy story about a school show where a small mistake becomes the funniest part and everyone ends up laughing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    show: Show = world.facts["show"]
    prop: Prop = world.facts["prop"]
    gag: Gag = world.facts["gag"]
    qa = [
        QAItem(
            question=f"What did {hero.label} try to do on {show.place}?",
            answer=f"{hero.label} tried to elicit a laugh from {show.audience}. It started as a serious plan, but it turned funny when the prop and the joke caused trouble together.",
        ),
        QAItem(
            question=f"How did {helper.label}'s joke help the performance?",
            answer=f"{helper.label} gave the line '{gag.line}', which pushed the act in a silly direction. That helped the scene turn from nervous to funny.",
        ),
        QAItem(
            question=f"Why did {prop.label} matter in the story?",
            answer=f"{prop.label} was the prop that made the plan wobble, spill, or sparkle. The accident with it helped the laugh happen instead of stopping the show.",
        ),
    ]
    if world.facts.get("ending_laugh"):
        qa.append(QAItem(
            question=f"What changed by the end of the show?",
            answer=f"{hero.label} stopped worrying and began smiling at the crowd. The whole room laughed, so the ending proved the joke had worked after all.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    prop: Prop = world.facts["prop"]
    show: Show = world.facts["show"]
    out = [
        QAItem(
            question="What does elicit mean?",
            answer="To elicit something means to bring it out or make it happen, like eliciting a laugh from a crowd.",
        ),
        QAItem(
            question="What is a prop in a show?",
            answer="A prop is an object used during a performance. It helps the actors tell the story or make a joke funnier.",
        ),
        QAItem(
            question="Why can comedy be hard at first?",
            answer="Comedy can be hard because timing matters. A small mistake or a surprised reaction can sometimes be what finally makes people laugh.",
        ),
    ]
    if prop.kind == "box":
        out.append(QAItem(question="What is a box often used for on a stage?", answer="A box can hold props or become part of the joke if someone treats it like it is grand and important."))
    if "school" in show.tags:
        out.append(QAItem(question="What happens at a school show?", answer="People perform for an audience, and sometimes the funniest moment is the one nobody planned."))
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


ASP_RULES = r"""
show_place(SP) :- show(S), place(S, SP).
prop_kind(PK) :- prop(P), kind(P, PK).
gag_fit(S, P, G) :- show(S), prop(P), gag(G), not bad_fit(P, G).
bad_fit(P, serious_pie) :- kind(P, hat).
bad_fit(P, tiny_bow) :- kind(P, box).
valid(S, P, G) :- show(S), prop(P), gag(G), not bad_fit(P, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SHOWS.items():
        lines.append(asp.fact("show", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("audience", sid, s.audience))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("kind", pid, p.kind))
    for gid in GAGS:
        lines.append(asp.fact("gag", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    smoke_params = resolve_params(build_parser().parse_args([]), random.Random(7))
    try:
        sample = generate(smoke_params)
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if ok:
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
        print("OK: smoke test story generation succeeded.")
        return 0
    print("MISMATCH: ASP and Python combinations differ.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if (params.show, params.prop, params.gag) not in valid_combos():
        raise StoryError(explain_rejection(params.show, params.prop, params.gag))
    world = init_world(params)
    perform(world)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"  {e.id}: {' '.join(bits)}")
        print(f"  events: {sample.world.history}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(show="class_show", prop="banana_hat", gag="loud_whisper", hero="Mia", hero_type="girl", helper="Tess", helper_type="girl", audience="the class"),
    StoryParams(show="tiny_talent", prop="foam_shoes", gag="tiny_bow", hero="Finn", hero_type="boy", helper="Noah", helper_type="boy", audience="the whole school"),
    StoryParams(show="family_night", prop="sparkly_box", gag="serious_pie", hero="Ada", hero_type="girl", helper="Ben", helper_type="boy", audience="the cousins"),
]


def resolve_random_name(rng: random.Random, typ: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if typ == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.gag} on {p.prop} at {p.show}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
