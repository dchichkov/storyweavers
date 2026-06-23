#!/usr/bin/env python3
"""
storyworlds/worlds/scrounge_toy_library_mystery_to_solve_quest.py
=================================================================

A small bedtime-story world about a child in a toy library who scrounges for
clues, follows a quest, and solves a gentle mystery by listening to an inner
monologue.

Seed premise:
- Setting: toy library
- Features: Mystery to Solve, Quest, Inner Monologue
- Style: Bedtime Story
- Must use the word "scrounge"

This storyworld models a child and a helper in a toy library where a favorite
toy is missing. The child quietly scrounges through shelves, thinks in an inner
monologue, follows a short quest for clues, and discovers that the missing toy
was being cleaned and left with a librarian note. The world keeps meters for
physical search state and memes for feelings, so the prose follows what
happens, not a frozen template.
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

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
class Setting:
    place: str
    texture: str
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_toy: str
    missing_phrase: str
    clue_word: str
    hiding_place: str
    reveal_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    search_verb: str
    quest_phrase: str
    method_phrase: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    hint: str
    comfort_phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    mystery: str
    quest: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "toy_library": Setting(
        place="the toy library",
        texture="soft rugs and low shelves",
        quiet=True,
        affords={"search", "listen", "sort"},
    )
}

MYSTERIES = {
    "missing_train": Mystery(
        id="missing_train",
        missing_toy="tiny train",
        missing_phrase="the little red train",
        clue_word="label",
        hiding_place="the repair basket",
        reveal_phrase="was getting a clean cloth and a new wheel",
        tags={"train", "label", "clean"},
    ),
    "missing_bear": Mystery(
        id="missing_bear",
        missing_toy="plush bear",
        missing_phrase="the soft brown bear",
        clue_word="tag",
        hiding_place="the wash shelf",
        reveal_phrase="was having its coat brushed and mended",
        tags={"bear", "tag", "wash"},
    ),
    "missing_car": Mystery(
        id="missing_car",
        missing_toy="toy car",
        missing_phrase="the shiny blue car",
        clue_word="note",
        hiding_place="the check-out desk",
        reveal_phrase="was waiting for a battery",
        tags={"car", "note", "battery"},
    ),
}

QUESTS = {
    "search_clues": Quest(
        id="search_clues",
        search_verb="scrounge for clues",
        quest_phrase="a clue-quest through the shelves",
        method_phrase="read the labels, peek behind baskets, and listen for a hint",
        end_image="the child holding the toy beside a sleepy lamp",
        tags={"quest", "clues"},
    ),
    "follow_note": Quest(
        id="follow_note",
        search_verb="follow the note trail",
        quest_phrase="a paper-trail quest",
        method_phrase="follow the little notes tucked beside the books",
        end_image="the child smiling under a paper star",
        tags={"quest", "note"},
    ),
    "ask_kindly": Quest(
        id="ask_kindly",
        search_verb="ask softly",
        quest_phrase="a whisper-quest",
        method_phrase="ask the librarian and wait for the answer",
        end_image="the child nodding while the shelves glowed warm and gold",
        tags={"quest", "ask"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ava", "Mia", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Owen", "Jude", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            for quest in QUESTS:
                combos.append((setting, mystery, quest))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested toy-library mystery and quest combination does not fit the world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child in a toy library who scrounges for clues, follows a quest, and solves a gentle mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, quest = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        quest=quest,
        child_name=name,
        child_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def _search(world: World, child: Entity, helper: Entity, mystery: Mystery, quest: Quest) -> None:
    child.meters["searching"] += 1
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"In {world.setting.place}, {child.id} and {helper.id} began a quiet quest among {world.setting.texture}."
    )
    world.say(
        f"{child.id} wanted to {quest.search_verb}, because {mystery.missing_phrase} was nowhere on the top shelf."
    )


def _inner_monologue(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["thinking"] += 1
    child.memes["hope"] += 1
    world.say(
        f'Inside {child.id}\'s head, a small voice said, "If I were {mystery.missing_phrase}, where would I hide?"'
    )
    world.say(
        f"{child.id} thought of a clue-word like a tiny lantern: maybe a {mystery.clue_word} could lead the way."
    )


def _scrounge(world: World, child: Entity, helper: Entity, quest: Quest) -> None:
    child.meters["scrounged"] += 1
    world.say(
        f"{child.id} began to scrounge gently, checking under pillows, beside baskets, and behind soft board books."
    )
    world.say(
        f"{helper.id} helped by keeping the whisper-quest calm: they knew {quest.method_phrase}."
    )


def _solve(world: World, child: Entity, mystery: Mystery, quest: Quest) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.meters["found"] += 1
    world.say(
        f"At last, a tiny clue led to {mystery.hiding_place}, and there was the answer."
    )
    world.say(
        f"{mystery.missing_phrase} {mystery.reveal_phrase}, so the mystery was solved without any hurry."
    )
    world.say(
        f"{quest.end_image} while the toy library stayed as quiet as a bedtime song."
    )


def tell(setting: Setting, mystery: Mystery, quest: Quest, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender))
    librarian = world.add(Entity(id="Librarian", kind="character", type="adult", label="the librarian"))

    child.meters = {"searching": 0.0, "scrounged": 0.0, "found": 0.0}
    child.memes = {"curiosity": 0.0, "worry": 0.0, "thinking": 0.0, "hope": 0.0, "relief": 0.0, "joy": 0.0}
    helper.meters = {"searching": 0.0}
    helper.memes = {"calm": 0.0}
    librarian.memes = {"kindness": 1.0}

    world.say(
        f"One sleepy evening, {child.id} came to {world.setting.place}, where the shelves were lined with toys waiting for bedtime stories."
    )
    world.say(
        f"{child.id} noticed that {mystery.missing_phrase} was gone, and a little mystery twinkled in {child.pronoun('possessive')} mind."
    )
    world.para()
    _search(world, child, helper, mystery, quest)
    _inner_monologue(world, child, mystery)
    _scrounge(world, child, helper, quest)
    world.para()
    world.say(
        f"Then {librarian.id} smiled softly and pointed toward a side table, because {mystery.missing_phrase} had a kind reason for being away."
    )
    _solve(world, child, mystery, quest)

    world.facts.update(
        child=child,
        helper=helper,
        librarian=librarian,
        mystery=mystery,
        quest=quest,
        setting=setting,
        resolved=True,
    )
    return world


KNOWLEDGE = {
    "train": [("What is a toy train?", "A toy train is a small toy that looks like a train. Children can roll it along tracks or floors.")],
    "bear": [("What is a plush bear?", "A plush bear is a soft stuffed toy bear. It is cozy to hold and hug.")],
    "car": [("What is a toy car?", "A toy car is a small car made for play. It can be pushed or rolled along the floor.")],
    "label": [("What is a label?", "A label is a little tag or name on something. It helps people know where it belongs.")],
    "tag": [("What is a tag on a toy?", "A tag is a small piece of paper or cloth that gives information about the toy.")],
    "note": [("What is a note?", "A note is a short piece of writing that can tell you something important.")],
    "clean": [("Why do toys get cleaned?", "Toys get cleaned so they stay nice, fresh, and ready for the next child.")],
    "wash": [("Why might a toy go to the wash shelf?", "Sometimes a toy goes to the wash shelf when it needs to be cleaned or mended.")],
    "battery": [("What does a battery do?", "A battery gives power to some toys so they can light up, move, or make sounds.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story set in {f["setting"].place} about a child who must solve a gentle mystery and includes the word "scrounge".',
        f"Tell a quiet quest story where {f['child'].id} follows a clue in the toy library and finds {f['mystery'].missing_phrase}.",
        f"Write a soft mystery tale with an inner monologue, a small search, and a happy ending in the toy library.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"What kind of place was {f['setting'].place} in the story?",
            answer="It was a quiet toy library with soft rugs and low shelves. It felt like a bedtime place, not a noisy one.",
        ),
        QAItem(
            question=f"What was missing when {child.id} arrived?",
            answer=f"{mystery.missing_phrase} was missing, and that started the little mystery. The missing toy made {child.id} want to search carefully.",
        ),
        QAItem(
            question=f"What did {child.id} do to look for the clue?",
            answer=f"{child.id} began to scrounge gently and follow {quest.quest_phrase}. That careful search helped the answer come into view.",
        ),
        QAItem(
            question=f"What did {child.id} think about in {child.pronoun('possessive')} inner monologue?",
            answer=f"{child.id} imagined where {mystery.missing_phrase} might hide and thought about the clue-word {mystery.clue_word}. That quiet thinking helped {child.id} keep going.",
        ),
        QAItem(
            question=f"Why did {helper.id} stay with {child.id} during the quest?",
            answer=f"{helper.id} helped keep the search calm and steady. Together they could follow the clue without turning the story noisy or rushed.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"A clue led them to {mystery.hiding_place}, and the missing toy was found there. The answer showed that the toy had simply been away for a kind reason.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and happy once the mystery was solved. The last scene was calm, warm, and sleepy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["quest"].tags)
    out: list[QAItem] = []
    for tag in ["train", "bear", "car", "label", "tag", "note", "clean", "wash", "battery"]:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        lines.append(
            f"  {e.id:10} ({e.kind:9}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="toy_library", mystery="missing_train", quest="search_clues", child_name="Mina", child_gender="girl", helper_name="Theo", helper_gender="boy"),
    StoryParams(setting="toy_library", mystery="missing_bear", quest="follow_note", child_name="Leo", child_gender="boy", helper_name="Nora", helper_gender="girl"),
    StoryParams(setting="toy_library", mystery="missing_car", quest="ask_kindly", child_name="Ava", child_gender="girl", helper_name="Finn", helper_gender="boy"),
]


def explain_invalid() -> str:
    return "(No story: the toy-library mystery needs the child, helper, clue, and quest to fit together.)"


ASP_RULES = r"""
mystery(setting,toy_library) :- setting(toy_library).
valid(setting,toy_library,mystery,quest) :- mystery(_,m), quest(_,q), place(toy_library), m != "", q != "".
solved :- found(clue), followed(quest), revealed(answer).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "toy_library")]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in m.tags:
            lines.append(asp.fact("tag", mid, tag))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in q.tags:
            lines.append(asp.fact("tag", qid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combo sets differ.")
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        ok = False
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    mystery = MYSTERIES.get(params.mystery)
    quest = QUESTS.get(params.quest)
    if setting is None or mystery is None or quest is None:
        raise StoryError(explain_invalid())
    world = tell(setting, mystery, quest, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.mystery} / {p.quest}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
