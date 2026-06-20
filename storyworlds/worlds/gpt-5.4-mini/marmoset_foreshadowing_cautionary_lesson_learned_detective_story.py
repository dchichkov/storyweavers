#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marmoset_foreshadowing_cautionary_lesson_learned_detective_story.py
====================================================================================================

A standalone tiny storyworld in a detective-story style.

Premise
-------
A small detective investigates a missing snack in a treehouse zoo club. A clever
marmoset, a few foreshadowing clues, and a cautionary mistake lead to a lesson
learned about asking for help before touching evidence.

This world models a child-facing detective mystery with:
- typed entities that carry physical meters and emotional memes,
- state-driven narration,
- a simple causal model,
- a reasonableness gate,
- a Python/ASP twin for parity checks,
- and three Q&A sets grounded in simulated state.

The world is intentionally small:
- one child detective,
- one animal witness (the marmoset),
- one adult helper,
- one missing item,
- one risky choice,
- one warning sign,
- one turn,
- one lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/marmoset_foreshadowing_cautionary_lesson_learned_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/marmoset_foreshadowing_cautionary_lesson_learned_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/marmoset_foreshadowing_cautionary_lesson_learned_detective_story.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/marmoset_foreshadowing_cautionary_lesson_learned_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"track": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    place: str
    perch: str
    clue: str
    missing_item: str
    risky_move: str
    warning_sign: str
    safe_tool: str
    lesson_line: str


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("alarm", 0.0) < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("detective").memes["focus"] += 1
        out.append("__worry__")
    return out


def _r_marmoset_notice(world: World) -> list[str]:
    out: list[str] = []
    m = world.entities.get("marmoset")
    if not m:
        return out
    if m.meters.get("saw_sign", 0.0) < THRESHOLD:
        return out
    sig = ("notice", "marmoset")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["suspicion"] += 1
    out.append("__notice__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("notice", "social", _r_marmoset_notice),
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


def clue_at_risk(scene: Scene) -> bool:
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def evidence_severity(delay: int) -> int:
    return 1 + delay


def is_safe(response: Response, delay: int) -> bool:
    return response.power >= evidence_severity(delay)


def predict(world: World, scene: Scene) -> dict:
    sim = world.copy()
    _step_investigate(sim, scene, narrate=False)
    return {
        "trouble": sim.get("detective").memes.get("trouble", 0.0),
        "found": sim.get("detective").meters.get("found", 0.0),
    }


def _step_investigate(world: World, scene: Scene, narrate: bool = True) -> None:
    det = world.get("detective")
    det.memes["curiosity"] += 1
    det.meters["found"] += 1
    if narrate:
        world.say(f"{det.id} searched the {scene.place} and followed the little clues.")


def setup(world: World, scene: Scene, detective: Entity, marmoset: Entity, adult: Entity) -> None:
    world.say(
        f"At {scene.place}, {detective.id} was playing detective, and the tiny zoo club had a mystery."
    )
    world.say(
        f"A marmoset sat on {scene.perch}, and something about {scene.clue} made {detective.id} stop and stare."
    )
    marmoset.meters["foreshadow"] += 1
    detective.memes["curiosity"] += 1


def foreshadow(world: World, scene: Scene, detective: Entity, marmoset: Entity) -> None:
    detective.meters["heard_hint"] += 1
    world.say(
        f"Then {scene.warning_sign} gave a tiny warning, like a clue in a casebook."
    )
    world.say(
        f"{detective.id} noticed that the marmoset kept glancing at the same spot, as if it knew something important."
    )


def caution(world: World, detective: Entity, adult: Entity, scene: Scene) -> None:
    detective.memes["worry"] += 1
    world.say(
        f'{detective.id} whispered, "This feels like a clue, but I should not touch it by myself."'
    )
    world.say(
        f'{adult.label_word.capitalize()} nodded and said the safest detectives ask a grown-up before moving evidence.'
    )


def mistake(world: World, detective: Entity, scene: Scene, delay: int) -> None:
    detective.memes["alarm"] += 1
    detective.meters["track"] += 1
    if delay:
        world.say(
            f"But {detective.id} waited too long, and the little mess became harder to sort out."
        )
    world.say(
        f"{detective.id} brushed the {scene.missing_item} aside, and a fresh set of tracks appeared in the dust."
    )
    propagate(world, narrate=False)


def rescue(world: World, adult: Entity, response: Response, scene: Scene) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came over at once and {response.text.replace('{item}', scene.missing_item)}."
    )
    world.say(
        f"The case was safe again, and the clue could be read clearly without getting ruined."
    )


def rescue_fail(world: World, adult: Entity, response: Response, scene: Scene) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came running and {response.fail.replace('{item}', scene.missing_item)}."
    )
    world.say(
        f"The clue was smeared, and the detective had to back up and start again from the beginning."
    )


def lesson(world: World, detective: Entity, adult: Entity, marmoset: Entity, scene: Scene) -> None:
    detective.memes["lesson"] += 1
    detective.memes["relief"] += 1
    world.say("For a moment, the room went quiet.")
    world.say(
        f"Then {adult.label_word.capitalize()} smiled and explained, "
        f'"A good detective looks carefully, remembers the warning, and asks for help before touching a clue."'
    )
    world.say(
        f"{detective.id} nodded, and even the marmoset looked calmer than before."
    )
    world.say(scene.lesson_line)


def ending_image(world: World, detective: Entity, marmoset: Entity) -> None:
    world.say(
        f"In the end, {detective.id} held the notebook, the marmoset swung from the perch, and the real clue stayed safe."
    )


def tell(scene: Scene, response: Response, detective_name: str = "Mia", detective_gender: str = "girl",
         adult_type: str = "mother", delay: int = 0) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    marmoset = world.add(Entity(id="marmoset", kind="character", type="animal", role="witness", label="the marmoset"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, role="helper"))

    setup(world, scene, detective, marmoset, adult)
    world.para()
    foreshadow(world, scene, detective, marmoset)
    caution(world, detective, adult, scene)
    mistake(world, detective, scene, delay)
    world.para()
    if is_safe(response, delay):
        rescue(world, adult, response, scene)
    else:
        rescue_fail(world, adult, response, scene)
    lesson(world, detective, adult, marmoset, scene)
    world.para()
    ending_image(world, detective, marmoset)

    world.facts.update(
        detective=detective,
        marmoset=marmoset,
        adult=adult,
        scene=scene,
        response=response,
        delay=delay,
        outcome="safe" if is_safe(response, delay) else "messy",
    )
    return world


SCENES = {
    "treehouse": Scene(
        place="the treehouse",
        perch="a high branch outside the window",
        clue="one peeled banana and a bent leaf",
        missing_item="the snack jar",
        risky_move="poke at the evidence",
        warning_sign="a tiny note pinned to the corkboard",
        safe_tool="tweezers",
        lesson_line="That was the first lesson learned: clues should be handled gently.",
    ),
    "museum": Scene(
        place="the museum corner",
        perch="a rope bridge above the display",
        clue="a trail of crumbs near the glass case",
        missing_item="the cookie tin",
        risky_move="reach across the case",
        warning_sign="a red ribbon around the table leg",
        safe_tool="a spoon",
        lesson_line="That was the lesson learned: careful hands solve more mysteries than quick hands.",
    ),
    "garden_shed": Scene(
        place="the garden shed",
        perch="a low shelf beside the seed packets",
        clue="a line of paw prints beside the flour sack",
        missing_item="the jam jar",
        risky_move="lift the lid too fast",
        warning_sign="a chalk arrow on the floorboards",
        safe_tool="a brush",
        lesson_line="That was the cautionary lesson: slow detectives keep the best clues intact.",
    ),
}

RESPONSES = {
    "tweezers": Response(
        "tweezers", 3, 3,
        "used the tweezers to lift the little clue back into place without touching it",
        "tried to use the tweezers, but the clue had already been smeared all over",
        "used the tweezers to move the clue safely",
    ),
    "brush": Response(
        "brush", 3, 2,
        "used a soft brush to clear the dust and keep the clue neat",
        "used a soft brush, but the dust had already scattered too far",
        "used a soft brush to clear the clue",
    ),
    "gloves": Response(
        "gloves", 2, 2,
        "put on gloves and lifted the clue carefully from the table",
        "put on gloves, but the clue was already ruined",
        "put on gloves and handled the clue carefully",
    ),
    "napkin": Response(
        "napkin", 1, 1,
        "wrapped the clue in a napkin",
        "wrapped the clue in a napkin, but that did not help at all",
        "wrapped the clue in a napkin",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Theo", "Ava", "Finn", "Ella", "Max"]
TRAITS = ["careful", "curious", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid in SCENES:
        for rid, resp in RESPONSES.items():
            if resp.sense >= SENSE_MIN:
                out.append((sid, rid))
    return out


@dataclass
class StoryParams:
    scene: str
    response: str
    detective_name: str
    detective_gender: str
    adult_type: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with a marmoset, clues, and lessons.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': too weak for this story.)")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, response = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(scene, response, name, gender, adult, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    response = f["response"]
    return [
        f'Write a child-friendly detective story set in {scene.place} that includes a marmoset and a foreshadowing clue.',
        f"Tell a cautionary mystery where a young detective almost mishandles evidence in {scene.place}, then learns a lesson learned.",
        f'Write a short detective story that includes the word "marmoset" and ends with the clue staying safe.',
        f"Make the rescue use {response.id} as the careful tool that solves the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    adult = f["adult"]
    scene = f["scene"]
    response = f["response"]
    marmoset = f["marmoset"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {detective.id}, a small detective, and the marmoset who helped point the way to the clue. {adult.label_word.capitalize()} was there too, because a careful mystery needs a grown-up helper."
        ),
        QAItem(
            question="What warning did the detective notice before touching the clue?",
            answer=f"The detective noticed {scene.warning_sign}. That was the foreshadowing, because it hinted that the clue should be handled gently."
        ),
        QAItem(
            question="What happened when the detective made the risky choice?",
            answer=f"{detective.id} brushed the {scene.missing_item} aside and made new tracks in the dust. That was the cautionary turn, because the clue became harder to use right away."
        ),
    ]
    if f["outcome"] == "safe":
        items.append(QAItem(
            question="How was the problem solved?",
            answer=f"{adult.label_word.capitalize()} used {response.qa_text} so the clue stayed safe. The careful tool solved the mystery without ruining the evidence."
        ))
    else:
        items.append(QAItem(
            question="How did the mistake change the case?",
            answer=f"The clue was smeared, so {adult.label_word} had to back up and start again. The detective learned that quick hands can make a mystery harder."
        ))
    items.append(QAItem(
        question="What lesson was learned at the end?",
        answer=f"The detective learned to look carefully, remember the warning, and ask for help before touching evidence. The ending proves the lesson because the notebook and the marmoset are still safe."
    ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marmoset?",
            answer="A marmoset is a tiny monkey with quick hands and a curious face. It can move fast and look very alert."
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery. Good detectives pay attention to small details."
        ),
        QAItem(
            question="Why should clues be handled gently?",
            answer="Clues can be broken, smudged, or moved by accident. If that happens, it can be harder to solve the mystery."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, R) :- scene(S), sensible(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for this detective mystery.)"


def explain_rejection() -> str:
    return "(No valid combination matches the given options.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene],
        RESPONSES[params.response],
        params.detective_name,
        params.detective_gender,
        params.adult_type,
        params.delay,
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


CURATED = [
    StoryParams("treehouse", "tweezers", "Mia", "girl", "mother", 0),
    StoryParams("museum", "brush", "Leo", "boy", "father", 1),
    StoryParams("garden_shed", "gloves", "Nora", "girl", "mother", 0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"compatible combos: {len(asp_valid_combos())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
