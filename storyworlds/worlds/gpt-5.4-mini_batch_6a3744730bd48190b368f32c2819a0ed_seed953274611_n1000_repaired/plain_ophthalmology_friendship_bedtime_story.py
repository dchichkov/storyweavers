#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/plain_ophthalmology_friendship_bedtime_story.py
===============================================================================

A tiny storyworld for a bedtime-style friendship tale about a child, a plain
little problem, and a gentle trip to ophthalmology.

Premise:
- A child gets a small eye discomfort after a plain dusty evening.
- A friend notices, stays kind, and helps them ask a grown-up.
- A calm ophthalmology visit fixes the worry.
- The friends end the night safe, sleepy, and relieved.

This script is standalone and uses only the stdlib plus the shared Storyweavers
result containers. The ASP twin mirrors the same compatibility and outcome logic.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    role: str = ""
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
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
    label: str
    calm_detail: str
    bedtime_detail: str
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
class EyeIssue:
    id: str
    label: str
    plain_word: str
    worry: str
    signs: str
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
class FriendAction:
    id: str
    label: str
    help_text: str
    talk_text: str
    success_text: str
    power: int
    sense: int
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
    setting: str
    issue: str
    helper: str
    action: str
    child: str
    child_type: str
    friend: str
    friend_type: str
    grownup: str
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
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "plain": Setting(
        id="plain",
        label="the plain",
        calm_detail="The plain was wide and quiet, with soft grass and a pale sky.",
        bedtime_detail="The night on the plain felt gentle, like a blanket laid over the land.",
    ),
    "garden": Setting(
        id="garden",
        label="the garden",
        calm_detail="The garden was small and still, with sleepy flowers and a warm porch light.",
        bedtime_detail="The garden at night looked soft and blue, almost like a dream.",
    ),
    "windowseat": Setting(
        id="windowseat",
        label="the window seat",
        calm_detail="The window seat was plain and tidy, with a pillow and a little lamp nearby.",
        bedtime_detail="The window seat was perfect for a bedtime story and a quiet breath.",
    ),
}

ISSUES = {
    "dusty_eye": EyeIssue(
        id="dusty_eye",
        label="a dusty eye",
        plain_word="plain",
        worry="their eye felt scratchy after the dust blew by",
        signs="their eye was red and blinking a lot",
        tags={"plain", "eye", "dust"},
    ),
    "sleepy_blur": EyeIssue(
        id="sleepy_blur",
        label="sleepy blur",
        plain_word="plain",
        worry="the world looked a little blurry after a long day",
        signs="they kept rubbing their eyes and squinting",
        tags={"plain", "eye", "sleep"},
    ),
}

HELPERS = {
    "kind_note": FriendAction(
        id="kind_note",
        label="a kind note",
        help_text="wrote a kind note that said, 'Let's ask a grown-up together.'",
        talk_text="reminded their friend that asking for help is brave",
        success_text="helped them remember to stay calm and ask for help",
        power=2,
        sense=3,
        tags={"friendship", "kind"},
    ),
    "cool_cloth": FriendAction(
        id="cool_cloth",
        label="a cool cloth",
        help_text="brought a cool cloth and let their friend rest for a moment",
        talk_text="told their friend to blink slowly and breathe",
        success_text="made the eye feel a little better while they waited",
        power=1,
        sense=2,
        tags={"friendship", "care"},
    ),
    "doctor_visit": FriendAction(
        id="doctor_visit",
        label="an ophthalmology visit",
        help_text="went with their friend to ophthalmology",
        talk_text="said the eye doctor would know just what to do",
        success_text="let the doctor wash away the problem and check the eye safely",
        power=4,
        sense=4,
        tags={"ophthalmology", "doctor"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Max", "Sam", "Finn"]
TRAITS = ["gentle", "curious", "kind", "careful", "soft-spoken", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid in ISSUES:
            for hid in HELPERS:
                combos.append((sid, iid, hid))
    return combos


def explain_rejection(issue: EyeIssue, helper: FriendAction) -> str:
    if "ophthalmology" not in helper.tags and helper.power < 2:
        return "(No story: the helper is too weak to make a meaningful bedtime turn.)"
    return "(No story: this combination does not make a gentle friendship-into-ophthalmology story.)"


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.action]
    return "fixed" if helper.power >= 2 else "softened"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime friendship story about a plain eye worry and an ophthalmology visit."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--action", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--friend")
    ap.add_argument("--grownup", choices=["mother", "father", "grandma", "grandpa"])
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


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.action and args.helper != args.action:
        raise StoryError("Choose the same helper and action, or leave one unspecified.")
    action = args.action or args.helper or rng.choice(sorted(HELPERS))
    helper = args.helper or action
    if helper != action:
        raise StoryError("The chosen helper/action pair must match.")

    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, issue, helper_id = rng.choice(sorted(combos))

    child_type = rng.choice(["girl", "boy"])
    friend_type = "girl" if child_type == "boy" else "boy"
    child = args.child or pick_name(rng, child_type)
    friend = args.friend or pick_name(rng, friend_type, avoid=child)
    grownup = args.grownup or rng.choice(["mother", "father", "grandma", "grandpa"])
    return StoryParams(
        setting=setting,
        issue=issue,
        helper=helper_id,
        action=action,
        child=child,
        child_type=child_type,
        friend=friend,
        friend_type=friend_type,
        grownup=grownup,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    issue = ISSUES[params.issue]
    action = HELPERS[params.action]
    world = World()
    child = world.add(Entity(id=params.child, kind="character", role="child", type=params.child_type))
    friend = world.add(Entity(id=params.friend, kind="character", role="friend", type=params.friend_type))
    grownup = world.add(Entity(id=params.grownup, kind="character", role="grownup", type=params.grownup))
    eye = world.add(Entity(id="eye_worry", kind="thing", label=issue.label, type="thing"))

    child.memes["worry"] = 1
    friend.memes["kindness"] = 1

    world.say(
        f"On the {setting.label}, {child.id} and {friend.id} shared a quiet evening. "
        f"{setting.calm_detail}"
    )
    world.say(
        f"{child.id} had {issue.label}, because {issue.worry}. "
        f"{friend.id} noticed right away and stayed close."
    )
    world.para()
    world.say(
        f'"The problem is very {issue.plain_word}," {friend.id} said softly. '
        f"{friend.id} {action.talk_text}."
    )
    if action.id == "kind_note":
        world.say(f"{friend.id} {action.help_text}.")
    elif action.id == "cool_cloth":
        world.say(f"{friend.id} {action.help_text}.")
    else:
        world.say(f"{friend.id} {action.help_text}.")
    world.say(
        f"{child.id} blinked, and {child.pronoun('possessive')} eye was still "
        f"{issue.signs}."
    )
    world.para()
    world.say(
        f"Then they told {grownup.id}, and soon the family went to ophthalmology. "
        f"There, a careful doctor looked at the eye and smiled."
    )
    if action.id == "doctor_visit":
        world.say(
            f"At ophthalmology, the doctor could clean the eye gently and check it safely. "
            f"{action.success_text.capitalize()}."
        )
        child.meters["fixed"] = 1
        friend.meters["fixed"] = 1
    else:
        world.say(
            f"The doctor saw the small trouble, gave kind advice, and the eye began to feel better. "
            f"{action.success_text.capitalize()}."
        )
        child.meters["softened"] = 1
        friend.meters["softened"] = 1
    world.para()
    world.say(
        f"By bedtime, {child.id} rested beside {friend.id}, both of them calm and sleepy. "
        f"The plain little worry was gone, and the night felt safe again."
    )
    world.facts.update(
        child=child, friend=friend, grownup=grownup, setting=setting, issue=issue,
        action=action, outcome=outcome_of(params), ophthalmology=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a child that includes the words "plain" and "ophthalmology" and shows a friendship helping someone feel safe.',
        f"Tell a gentle friendship story where {f['child'].id} has a plain eye worry, {f['friend'].id} helps, and the family goes to ophthalmology.",
        f"Write a sleepy, comforting story about a small eye problem, a kind friend, and a calm ophthalmology visit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    issue: EyeIssue = f["issue"]
    action: FriendAction = f["action"]
    qa = [
        QAItem(
            question=f"What was wrong with {child.id}?",
            answer=f"{child.id} had {issue.label}. It was a plain little worry, and their eye looked red and blinked a lot.",
        ),
        QAItem(
            question=f"How did {friend.id} help {child.id}?",
            answer=f"{friend.id} stayed kind, talked gently, and used {action.label} to help. They also stayed with {child.id} until a grown-up could help.",
        ),
        QAItem(
            question="Why did they go to ophthalmology?",
            answer="They went to ophthalmology so a doctor who knows eyes could look at the problem. That was the safest way to make sure the eye got better.",
        ),
    ]
    if f["outcome"] == "fixed":
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the eye feeling better and both friends getting sleepy and calm. The plain worry was fixed, and bedtime felt peaceful again.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the worry softening and the friends feeling calmer. The bedtime mood was gentle and safe, even before everything was fully fixed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ophthalmology?",
            answer="Ophthalmology is the part of medicine that helps doctors look after eyes. An ophthalmology visit is a safe place to get help when an eye hurts or seems wrong.",
        ),
        QAItem(
            question="Why is friendship important in a bedtime story?",
            answer="Friendship makes a scary or plain little problem feel smaller. A kind friend can sit close, speak gently, and help someone ask for help.",
        ),
        QAItem(
            question="What does plain mean here?",
            answer="Plain means simple and not fancy. In this story, the plain part helps make the worry feel ordinary, calm, and easy to understand.",
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting(S), issue(I), helper(H)) :- setting(S), issue(I), helper(H).
outcome(fixed) :- helper(doctor_visit).
outcome(softened) :- helper(kind_note).
outcome(softened) :- helper(cool_cloth).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in ISSUES:
        lines.append(asp.fact("issue", i))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program(f"{asp.fact('helper', params.action)}", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python combo gates match.")
    else:
        print("MISMATCH: ASP and Python combo gates differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.issue not in ISSUES:
        raise StoryError("Unknown issue.")
    if params.action not in HELPERS:
        raise StoryError("Unknown helper/action.")
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


CURATED = [
    StoryParams(
        setting="plain",
        issue="dusty_eye",
        helper="kind_note",
        action="kind_note",
        child="Lily",
        child_type="girl",
        friend="Ben",
        friend_type="boy",
        grownup="mother",
    ),
    StoryParams(
        setting="windowseat",
        issue="sleepy_blur",
        helper="doctor_visit",
        action="doctor_visit",
        child="Mia",
        child_type="girl",
        friend="Theo",
        friend_type="boy",
        grownup="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
