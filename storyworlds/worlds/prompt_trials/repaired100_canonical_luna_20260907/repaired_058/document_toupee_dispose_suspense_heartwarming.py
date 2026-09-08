#!/usr/bin/env python3
"""
A heartwarming suspense storyworld about a lost document, a borrowed toupee,
and a careful choice about what to dispose of.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Theo"
    elder: str = "Grandpa Sol"
    place: str = "the little community theater"
    document: str = "the theater's old welcome letter"
    toupee: str = "a soft silver toupee"
    task: str = "prepare the theater for its first reunion night"


@dataclass(frozen=True)
class Incident:
    title: str
    problem: str
    fear: str
    clue: str
    suspense: str
    cause: str
    helper_job: str
    hero_job: str
    repair: str
    lesson: str
    ending: str


INCIDENTS = [
    Incident(
        "The Vanishing Welcome Letter",
        "the theater's welcome document disappeared just before the reunion",
        "someone feared that an important promise had been thrown away",
        "a thin trail of blue paper fibers led behind the costume rack",
        "a draft lifted the rack curtain while the lights flickered",
        "the document had slipped inside a costume box when the old cabinet was moved",
        "held the flashlight steady and checked each box without tearing the papers",
        "read the document aloud and marked its safe place",
        "they found the letter, placed it in a clear folder, and saved the reunion",
        "Careful searching protects both precious memories and the people who keep them.",
        "the welcome letter rested beneath glass while neighbors entered smiling",
    ),
    Incident(
        "The Silver Disguise",
        "a silver toupee meant for the comedy show could not be found",
        "Luna worried that the missing prop would embarrass Grandpa Sol on stage",
        "a strand of silver hair caught on the handle of the document drawer",
        "the backstage door creaked although nobody seemed to be there",
        "the toupee had been tucked into the drawer to keep it safe from dust",
        "watched the doorway and kept the search calm",
        "asked before opening the drawer and returned the toupee to its labeled box",
        "they brushed the prop gently and gave Grandpa Sol time to choose whether to wear it",
        "A kind choice lets people feel safe even when a surprise is waiting.",
        "Grandpa Sol bowed beneath the silver toupee while Luna applauded from the wings",
    ),
    Incident(
        "The Wrong Disposal Box",
        "a box marked DISPOSE stood beside a box holding old theater documents",
        "Theo feared that the treasured records had been placed with rubbish",
        "the disposal label was written on a loose card, not painted on the box",
        "the recycling truck was already humming beyond the courtyard gate",
        "a volunteer had moved the label while sorting empty packing paper",
        "ran to pause the truck and explained why the boxes needed checking",
        "opened the records box carefully and separated true rubbish from history",
        "they replaced the loose card with clear labels and kept every useful document",
        "Before we dispose of something, we should know what it means and who may need it.",
        "the clean archive shelf glowed beside a small basket of properly sorted paper",
    ),
    Incident(
        "The Whisper Behind the Curtain",
        "a whisper seemed to name Luna from behind the stage curtain",
        "she thought someone had found the private document she carried for Grandpa Sol",
        "the whisper repeated whenever the old fan began to turn",
        "the curtain billowed toward the dark wings as the final key rattled",
        "the fan was pulling a paper strip across a loose sign",
        "checked the fan switch and kept the document in a closed folder",
        "read the sign, fixed its corner, and returned the private paper to its owner",
        "they laughed softly when the whisper stopped and promised to ask before guessing",
        "A frightening sound can have a simple cause, but checking together makes everyone braver.",
        "the quiet curtain framed a warm stage where the reunited neighbors sang",
    ),
    Incident(
        "The Pocketed Program",
        "the last printed program for the reunion was missing",
        "Grandpa Sol believed someone had taken it to hide a mistake",
        "a square corner of paper showed beneath the old toupee case",
        "the case rocked by itself when footsteps passed backstage",
        "the program had been used as a clean lining for the case",
        "held the case still and asked who had last carried it",
        "removed the program gently and replaced the lining with fresh paper",
        "they corrected the program's date and made enough copies for every guest",
        "Questions can uncover an innocent mistake before suspicion becomes a wound.",
        "every guest held a program as the silver prop waited safely in its case",
    ),
    Incident(
        "The Red Stamp",
        "a red stamp on the document looked like a warning to dispose of it",
        "Luna thought the theater's history had been rejected",
        "the stamp said COPY, not CANCEL, beneath a layer of dust",
        "the old projector clicked on and cast the red mark across the wall",
        "the document was a duplicate prepared for the archive, not a discarded original",
        "cleaned the glass and compared the pages side by side",
        "stored the original in the archive and recycled only the extra copy",
        "they labeled the folders so future readers would know which papers mattered",
        "Understanding a mark takes patience; a frightening symbol is not always bad news.",
        "the original document shone in its folder while the projector showed a gentle red glow",
    ),
    Incident(
        "The Empty Chair",
        "one chair near the document table was empty when the reunion began",
        "everyone feared the missing guest had been hurt backstage",
        "a folded toupee bag rested beside the chair",
        "the backstage bell rang once and then went silent",
        "Grandpa Sol had gone to help a shy neighbor choose a costume",
        "followed the bell's direction with a lantern",
        "left the chair ready and welcomed both guests when they returned",
        "they placed the toupee bag on a hook and saved a seat for every newcomer",
        "Waiting with care can be an act of welcome, not a sign that hope is gone.",
        "the empty chair filled with a smiling neighbor beneath the theater's golden lights",
    ),
    Incident(
        "The Crumpled Promise",
        "a crumpled document lay near the bin marked for disposal",
        "Theo thought the theater had decided to forget its oldest promise",
        "the crease matched the edge of a heavy toupee case",
        "the bin lid swung shut just as rain began tapping the roof",
        "the document had fallen when the case was lifted, but its writing was still clear",
        "kept the bin dry and gathered the loose pages",
        "flattened the document under a clean book and read it with its owner",
        "they mended the page with a sleeve and placed it in the archive",
        "A worn page can still carry a living promise.",
        "the repaired document stood beside fresh flowers at the theater entrance",
    ),
    Incident(
        "The Late Spotlight",
        "the spotlight came on by itself while Luna sorted papers",
        "she feared the empty stage was warning her to dispose of everything",
        "the switch had a strip of tape marked FOR REHEARSAL",
        "the spotlight shone across the toupee case like a bright white eye",
        "a loose cord had brushed the rehearsal switch",
        "unplugged the light safely and kept the papers away from the heat",
        "tested the cord with Theo and returned the documents to a cool cabinet",
        "they removed the loose tape and labeled the working switch clearly",
        "When a surprise makes us hurry, safe steps matter more than quick guesses.",
        "the spotlight warmed the stage only when the actors were ready",
    ),
    Incident(
        "The Last Little List",
        "a list of reunion guests vanished from the document table",
        "Grandpa Sol worried that someone had been forgotten",
        "a silver thread crossed the list's empty place",
        "the wind pushed the list toward the open stage door",
        "the toupee's storage bag had caught the list and carried it under a chair",
        "closed the door and searched beneath the chairs",
        "checked every name with the guests and added one neighbor who had just arrived",
        "they kept the list in a folder and invited the late neighbor warmly",
        "A list helps us remember people, but kindness helps us notice who is newly here.",
        "the final list grew longer as every guest found a place in the bright room",
    ),
]

OPENINGS = [
    "On a rainy afternoon",
    "As evening settled over the town",
    "Before the first curtain rose",
    "At the edge of a friendly neighborhood",
    "On the day of the theater reunion",
    "Beneath a sky full of pale clouds",
]

QUESTIONS = [
    "What do we know for sure, and what are we only fearing?",
    "Let us check the clue before we decide what happened.",
    "Could we pause the work and search safely together?",
    "Who last saw the document or the toupee?",
    "Let us protect the people and the memories while we investigate.",
]

TEAMWORK_IMAGES = [
    "Luna held the lantern while Theo checked the labels.",
    "They made a quiet three-step plan and followed it together.",
    "One person watched the door while the other searched.",
    "They placed every paper on a clean table before deciding its fate.",
    "They compared the clue with the room instead of trusting a hurried guess.",
]

PERSPECTIVES = [
    "The youngest volunteer remembered how gently everyone had spoken.",
    "Grandpa Sol said the repaired memory felt brighter than a new one.",
    "Theo kept the clear labels as a reminder of that suspenseful evening.",
    "Luna understood that kindness could turn a frightening search into a welcome.",
    "The neighbors thanked the children for protecting both truth and feelings.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    elder: Entity
    place: str
    document_safe: bool = False
    toupee_safe: bool = False
    disposal_checked: bool = False
    suspense: bool = False
    resolved: bool = False
    incident: Optional[Incident] = None
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming suspense story about a document and a toupee.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    ap.add_argument("--place")
    ap.add_argument("--document")
    ap.add_argument("--toupee")
    ap.add_argument("--task")
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Maya", "Nora", "Iris"]),
        helper=args.helper or rng.choice(["Theo", "Ben", "Sam", "Ari"]),
        elder=args.elder or rng.choice(["Grandpa Sol", "Aunt June", "Ms. Rowan"]),
        place=args.place or rng.choice(
            ["the little community theater", "the old library hall", "the neighborhood playhouse"]
        ),
        document=args.document or rng.choice(
            ["the theater's old welcome letter", "a family performance document", "the reunion guest list"]
        ),
        toupee=args.toupee or rng.choice(
            ["a soft silver toupee", "a curly brown toupee", "a bright blue stage toupee"]
        ),
        task=args.task or "prepare the theater for its first reunion night",
    )


def _validate(params: StoryParams) -> None:
    if not params.document.strip():
        raise StoryError("The story needs a document to protect.")
    if not params.toupee.strip():
        raise StoryError("The story needs a toupee as a stage prop.")
    forbidden = {"poison", "weapon", "dangerous"}
    if any(word in params.document.lower() or word in params.toupee.lower() for word in forbidden):
        raise StoryError("The document and toupee must remain gentle, safe story objects.")
    if params.hero.strip().lower() == params.helper.strip().lower():
        raise StoryError("The hero and helper need different names so their dialogue is clear.")


def _stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA17C42)
    text = "|".join(
        [params.hero, params.helper, params.elder, params.place, params.document, params.toupee, params.task]
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def _ground(incident: Incident, params: StoryParams) -> Incident:
    values = {
        "hero": params.hero,
        "helper": params.helper,
        "elder": params.elder,
        "document": params.document,
        "toupee": params.toupee,
    }
    updates = {
        name: getattr(incident, name).format(**values)
        for name in incident.__dataclass_fields__
        if name != "title"
    }
    return Incident(incident.title, **updates)


def _setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} and {p.helper} worked inside {p.place}. "
        f"They were helping {p.elder} {p.task}."
    )
    world.say(
        f"On a clean table lay {p.document}, while {p.toupee} waited in a labeled costume box. "
        "The old theater smelled of dust, rain, and warm wooden seats."
    )


def _trouble(world: World, incident: Incident) -> None:
    p = world.params
    world.para()
    world.suspense = True
    world.hero.add_meme("worry", 1)
    world.helper.add_meme("courage", 1)
    world.say(f"Then came {incident.title}. {incident.problem.capitalize()}.")
    world.say(f"{incident.fear.capitalize()}.")
    world.say(f"{incident.suspense}, and for one quiet moment nobody knew what to do.")
    world.say(f"{p.hero} whispered, \"What if we dispose of the wrong thing?\"")
    world.say(f"{p.helper} answered, \"We will not guess. We will look together.\"")


def _investigate(world: World, incident: Incident, question: str, method: str) -> None:
    p = world.params
    world.para()
    world.hero.add_meme("resolve", 1)
    world.helper.add_meme("resolve", 1)
    world.say(f"{p.hero} asked, \"{question}\"")
    world.say(f"{p.helper} replied, \"{method}\"")
    world.say(f"They found a useful clue: {incident.clue}.")
    world.say(f"That clue revealed the real cause: {incident.cause}.")
    world.say(
        f"{p.helper} {incident.helper_job}; {p.hero} {incident.hero_job}. "
        "The suspense eased as the room became understandable again."
    )


def _resolve(world: World, incident: Incident, perspective: str) -> None:
    p = world.params
    world.para()
    world.document_safe = True
    world.toupee_safe = True
    world.disposal_checked = True
    world.resolved = True
    world.hero.add_meter("care", 1)
    world.helper.add_meter("care", 1)
    world.say(f"Their careful work succeeded: {incident.repair}.")
    world.say(
        f"Nothing important was disposed of by mistake. {p.document.capitalize()} was safe, "
        f"and {p.toupee} was ready for the reunion."
    )
    world.say(f"{p.elder} said, \"{incident.lesson}\"")
    world.say(f"When the doors opened, {incident.ending} {perspective}")


def tell(params: StoryParams) -> World:
    _validate(params)
    world = World(
        params=params,
        hero=Entity(params.hero, "hero"),
        helper=Entity(params.helper, "helper"),
        elder=Entity(params.elder, "elder"),
        place=params.place,
    )
    rng = _stable_rng(params)
    incident = _ground(rng.choice(INCIDENTS), params)
    world.incident = incident
    _setup(world, rng.choice(OPENINGS))
    _trouble(world, incident)
    _investigate(world, incident, rng.choice(QUESTIONS), rng.choice(TEAMWORK_IMAGES))
    _resolve(world, incident, rng.choice(PERSPECTIVES))
    world.facts = {
        "document": params.document,
        "toupee": params.toupee,
        "place": params.place,
        "incident": incident.title,
        "problem": incident.problem,
        "clue": incident.clue,
        "cause": incident.cause,
        "repair": incident.repair,
        "lesson": incident.lesson,
        "document_safe": world.document_safe,
        "toupee_safe": world.toupee_safe,
        "disposal_checked": world.disposal_checked,
        "suspense": world.suspense,
        "resolved": world.resolved,
    }
    return world


ASP_RULES = r"""
document_present.
toupee_present.
suspense :- document_present, toupee_present, uncertain_disposal.
careful_search :- asks_question, checks_clue.
disposal_safe :- careful_search, separates_saved_items.
resolved :- suspense, disposal_safe, document_present, toupee_present.
#show suspense/0.
#show careful_search/0.
#show disposal_safe/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("document_present"),
            asp.fact("toupee_present"),
            asp.fact("uncertain_disposal"),
            asp.fact("asks_question"),
            asp.fact("checks_clue"),
            asp.fact("separates_saved_items"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception:
        print("ASP verification unavailable: clingo helper not installed.")
        return 1
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    expected = {"suspense", "careful_search", "disposal_safe", "resolved"}
    if expected.issubset(names):
        sample = generate(StoryParams(seed=17))
        if sample.world is not None and sample.world.resolved:
            print("OK: ASP and Python both reach a safe, resolved story.")
            return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a heartwarming suspense story about {p.hero} and {p.helper} protecting {p.document}.",
        f"Tell a gentle story where {p.toupee} causes a mystery and careful teamwork prevents the wrong disposal.",
        f"Write a child-friendly story set in {p.place} where a clue changes what the characters decide to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    incident = world.incident
    assert incident is not None
    return [
        QAItem(
            question="What created the suspense in the story?",
            answer=f"The suspense began because {incident.problem}. Everyone feared that something important might be lost.",
        ),
        QAItem(
            question="What clue helped the characters understand the mystery?",
            answer=f"They noticed that {incident.clue}. This clue led them toward the real cause: {incident.cause}.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.helper} work together?",
            answer=f"{p.helper} {incident.helper_job}; {p.hero} {incident.hero_job}. They investigated before deciding what to dispose of.",
        ),
        QAItem(
            question="What was kept safe?",
            answer=f"They kept {p.document} safe and made sure {p.toupee} was ready for the reunion.",
        ),
        QAItem(
            question="What did the characters learn?",
            answer=incident.lesson,
        ),
        QAItem(
            question="What final image showed that the problem was resolved?",
            answer=f"At the end, {incident.ending} The warm scene showed that the memories and the people were safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a document?",
            answer="A document is a paper or record that holds information, instructions, or memories.",
        ),
        QAItem(
            question="What does dispose mean?",
            answer="To dispose of something means to get rid of it, often by recycling it, throwing it away, or placing it somewhere appropriate.",
        ),
        QAItem(
            question="What is a toupee?",
            answer="A toupee is a small hairpiece worn on the head, sometimes as part of a costume.",
        ),
        QAItem(
            question="Why should people check before disposing of a document?",
            answer="They should check because the document may contain useful information or memories that someone still needs.",
        ),
        QAItem(
            question=f"Where did the story take place?",
            answer=f"The story took place in {p.place}, where the characters prepared for a warm community reunion.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in [world.hero, world.helper, world.elder]:
        lines.append(f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}")
    lines.append(
        "state: "
        f"suspense={world.suspense} document_safe={world.document_safe} "
        f"toupee_safe={world.toupee_safe} disposal_checked={world.disposal_checked} "
        f"resolved={world.resolved}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        seed=101,
        hero="Luna",
        helper="Theo",
        elder="Grandpa Sol",
        place="the little community theater",
        document="the theater's old welcome letter",
        toupee="a soft silver toupee",
    ),
    StoryParams(
        seed=202,
        hero="Maya",
        helper="Ari",
        elder="Aunt June",
        place="the old library hall",
        document="the reunion guest list",
        toupee="a bright blue stage toupee",
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def _asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspense/0.\n#show careful_search/0.\n#show disposal_safe/0.\n#show resolved/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        if not _asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.helper} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
