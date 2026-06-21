#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/simultaneous_survey_campus_twist_rhyming_story.py
==================================================================================

A small storyworld for a campus survey with a twist, told in a rhyming-story
style. Two students run simultaneous surveys across campus, expect one result,
and discover a surprising turn that changes the ending.

The world is built from typed entities with physical meters and emotional memes,
with a forward causal model, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RHYME_TRAIT = "rhyming"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"busy": 0.0, "found": 0.0, "tidy": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "surprise": 0.0, "joy": 0.0, "pride": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class CampusSite:
    id: str
    label: str
    clue: str
    twist_clue: str
    ripple: str
    kind: str
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
class Survey:
    id: str
    question: str
    answer_hint: str
    can_find: bool
    effort: int
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
class Twist:
    id: str
    reveal: str
    ending: str
    joy_bonus: int
    pride_bonus: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for e in list(world.entities.values()):
            if e.meters.get("found", 0) >= THRESHOLD and ("found", e.id) not in world.fired:
                world.fired.add(("found", e.id))
                e.memes["joy"] += 1
                out.append(f"{e.id} grinned as the clues lined up.")
                changed = True
        if world.facts.get("twist_seen") and ("twist",) not in world.fired:
            world.fired.add(("twist",))
            rep = world.get("runner")
            rep.memes["surprise"] += 1
            rep.memes["joy"] += 1
            world.get("campus").meters["tidy"] += 1
            out.append("The twist made the whole campus feel newly bright.")
            changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def survey_clue(site: CampusSite, survey: Survey) -> bool:
    return survey.can_find and site.kind == "campus" and site.id in {"quad", "library", "cafeteria"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for site in SITES:
        for survey in SURVEYS:
            for twist in TWISTS:
                if survey_clue(SITES[site], SURVEYS[survey]):
                    combos.append((site, survey, twist))
    return combos


@dataclass
class StoryParams:
    site: str
    survey: str
    twist: str
    runner_name: str
    partner_name: str
    runner_gender: str
    partner_gender: str
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


SITES = {
    "quad": CampusSite(
        id="quad", label="the quad", clue="the open quad",
        twist_clue="a secret note by the fountain", ripple="the grass looked neat again",
        kind="campus", tags={"campus", "survey"},
    ),
    "library": CampusSite(
        id="library", label="the library steps", clue="the quiet library steps",
        twist_clue="a bookmark tucked in a poem book", ripple="the stacks seemed to smile",
        kind="campus", tags={"campus", "survey"},
    ),
    "cafeteria": CampusSite(
        id="cafeteria", label="the cafeteria", clue="the lunch line",
        twist_clue="a tray with a hidden sticker", ripple="the tables shone in a row",
        kind="campus", tags={"campus", "survey"},
    ),
}

SURVEYS = {
    "song": Survey(id="song", question="what song students liked most", answer_hint="a tune", can_find=True, effort=1, tags={"survey"}),
    "snack": Survey(id="snack", question="which snack students loved best", answer_hint="a treat", can_find=True, effort=1, tags={"survey"}),
    "club": Survey(id="club", question="which club students wanted", answer_hint="a club", can_find=True, effort=1, tags={"survey"}),
}

TWISTS = {
    "switch": Twist(id="switch", reveal="the surprise was that the shy dean had filled out the survey too", ending="the shy dean laughed and joined the tune", joy_bonus=2, pride_bonus=2, tags={"twist"}),
    "double": Twist(id="double", reveal="the twist was that both teams found the same answer at the same time", ending="the two teams cheered as one", joy_bonus=1, pride_bonus=2, tags={"twist"}),
    "helper": Twist(id="helper", reveal="the twist was that a campus cat kept leading them to every clue", ending="the cat curled up like a tiny king", joy_bonus=2, pride_bonus=1, tags={"twist"}),
}

NAMES_GIRL = ["Maya", "Nina", "Lina", "Tessa", "Mila"]
NAMES_BOY = ["Eli", "Noah", "Owen", "Ari", "Finn"]
TRAITS = [RHYME_TRAIT, "bright", "kind", "quick"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campus survey twist storyworld.")
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--survey", choices=SURVEYS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--runner-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--runner-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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


def explain_rejection() -> str:
    return "(No story: the chosen campus survey would not plausibly lead to a clear twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.site is None or c[0] == args.site)
              and (args.survey is None or c[1] == args.survey)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError(explain_rejection())
    site, survey, twist = rng.choice(sorted(combos))
    runner_gender = args.runner_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if runner_gender == "girl" else "girl")
    runner_name = args.runner_name or rng.choice(NAMES_GIRL if runner_gender == "girl" else NAMES_BOY)
    partner_name = args.partner_name or rng.choice([n for n in (NAMES_BOY if partner_gender == "boy" else NAMES_GIRL) if n != runner_name])
    return StoryParams(
        site=site,
        survey=survey,
        twist=twist,
        runner_name=runner_name,
        partner_name=partner_name,
        runner_gender=runner_gender,
        partner_gender=partner_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    runner = world.add(Entity(id=params.runner_name, kind="character", type=params.runner_gender, role="runner"))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_gender, role="partner"))
    campus = world.add(Entity(id="campus", kind="place", type="campus", label="the campus"))
    site = SITES[params.site]
    survey = SURVEYS[params.survey]
    twist = TWISTS[params.twist]

    runner.memes["hope"] += 1
    partner.memes["hope"] += 1

    world.say(
        f"On a bright campus morning, {runner.id} and {partner.id} went in a swirl, "
        f"to do a simultaneous survey, with rhyme in their ear and spring in their twirl."
    )
    world.say(
        f"They asked about {survey.question}, then crossed the green lawn with a smile, "
        f"from {site.clue} to {site.label}, they measured each answer in style."
    )

    world.para()
    runner.meters["busy"] += 1
    partner.meters["busy"] += 1
    world.say(
        f"At {site.label}, {runner.id} noted each choice, and {partner.id} wrote in a neat little way, "
        f"but both of them noticed the same odd clue, that shimmered in the light of the day."
    )
    if site.id == "quad":
        world.say("A note near the fountain winked in the breeze, small as a leaf and sly.")
    elif site.id == "library":
        world.say("A bookmark hid in a poem book, as if it were waiting to fly.")
    else:
        world.say("A sticker on a tray had a secret small spark, like a star in a noon-time sky.")

    world.para()
    world.say(
        f"Then came the twist: {twist.reveal}. {twist.ending} "
        f"Their surprise turned the survey into a cheerful song, and the campus felt lighter along."
    )
    runner.memes["surprise"] += twist.joy_bonus
    partner.memes["surprise"] += twist.joy_bonus
    runner.memes["joy"] += twist.joy_bonus + 1
    partner.memes["joy"] += twist.joy_bonus + 1
    runner.memes["pride"] += twist.pride_bonus
    partner.memes["pride"] += twist.pride_bonus
    campus.meters["tidy"] += 1
    world.facts.update(
        runner=runner, partner=partner, campus=campus, site=site, survey=survey, twist=twist,
        twist_seen=True,
    )
    propagate(world)
    world.para()
    world.say(
        f"They finished their simultaneous survey hand in hand, with a skip and a grin, "
        f"and wrote the last answer together; the twist made the day bright from within."
    )
    world.say(
        f"By dusk, {site.ripple}, and {runner.id} and {partner.id} walked home with delight, "
        f"for the campus had kept its surprise, and the rhyme of the day ended right."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about a simultaneous campus survey that ends with a twist.',
        f"Tell a short rhyme where {f['runner'].id} and {f['partner'].id} do a survey on campus and discover a surprising reveal.",
        f'Create a child-friendly rhyming story that includes the words "simultaneous", "survey", and "campus", with a twist at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    runner, partner = f["runner"], f["partner"]
    site, survey, twist = f["site"], f["survey"], f["twist"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {runner.id} and {partner.id}, two students working together on campus. They took part in a simultaneous survey and kept the whole day moving in rhyme."
        ),
        QAItem(
            question="What were they doing?",
            answer=f"They were doing a survey about {survey.question}. They asked the questions at {site.label} while the other one wrote the answers, so the work happened at the same time."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {twist.reveal}. That surprise changed the survey from ordinary work into a happy little discovery."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a survey?", answer="A survey is a set of questions people ask to learn what others think or like. It helps gather answers from many people in an organized way."),
        QAItem(question="What does simultaneous mean?", answer="Simultaneous means happening at the same time. If two people do things simultaneously, they are both working together at once."),
        QAItem(question="What is a campus?", answer="A campus is the area where a school or college has its buildings, paths, and gathering places. People walk there to study, talk, and work."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what you expected. It makes the ending feel new and interesting."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S, Q, T) :- site(S), survey(Q), twist(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SITES:
        lines.append(asp.fact("site", sid))
    for qid in SURVEYS:
        lines.append(asp.fact("survey", qid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("py only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES or params.survey not in SURVEYS or params.twist not in TWISTS:
        raise StoryError("Invalid parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combo_for(site: CampusSite, survey: Survey, twist: Twist) -> bool:
    return site.kind == "campus" and survey.can_find and "twist" in twist.tags


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, t) for s in SITES for q in SURVEYS for t in TWISTS if valid_combo_for(SITES[s], SURVEYS[q], TWISTS[t])]


CURATED = [
    StoryParams(site="quad", survey="song", twist="switch", runner_name="Maya", partner_name="Eli", runner_gender="girl", partner_gender="boy"),
    StoryParams(site="library", survey="club", twist="double", runner_name="Noah", partner_name="Lina", runner_gender="boy", partner_gender="girl"),
    StoryParams(site="cafeteria", survey="snack", twist="helper", runner_name="Tessa", partner_name="Finn", runner_gender="girl", partner_gender="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.site is None or c[0] == args.site)
              and (args.survey is None or c[1] == args.survey)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("No valid combo matches the given options.")
    site, survey, twist = rng.choice(sorted(combos))
    runner_gender = args.runner_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    runner_name = args.runner_name or rng.choice(NAMES_GIRL if runner_gender == "girl" else NAMES_BOY)
    partner_name = args.partner_name or rng.choice(NAMES_GIRL if partner_gender == "girl" else NAMES_BOY)
    if partner_name == runner_name:
        partner_name = (NAMES_BOY if partner_gender == "boy" else NAMES_GIRL)[0]
    return StoryParams(
        site=site, survey=survey, twist=twist,
        runner_name=runner_name, partner_name=partner_name,
        runner_gender=runner_gender, partner_gender=partner_gender,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
