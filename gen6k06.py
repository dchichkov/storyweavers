"""
gen6k06.py - Quality-pass pack for the gen6 engine.

This pack does NOT add new kernel *names*; instead it adds **tolerant variants**
for high-frequency builtin kernels whose strict single signatures (defined in
`gen6.py`) failed to bind on the messy argument shapes that appear in the real
dataset, causing them to fall through to `fallback_text` and be rendered as
verbed nouns ("routined", "warninged", "joyed", "lossed", "lessoned",
"friendshiped") or as the generic "Something help happened" line.

Method (AGENTS.md "gen6 Quality Pass"): generated thousands of fully-covered
stories, tallied the worst recurring surface patterns, traced each to its root
cause, and added a permissive `*args`/`**kw` variant that produces good prose for
the off-canonical shapes. The dispatcher still prefers the precise typed builtin
when it fits (it binds more args / registers earlier), so canonical calls are
unchanged; these variants only catch what previously degraded to fallback.

Examples fixed:
    Joy(Lily, Mom)           "Lily joyed Mom."            -> "Lily and Mom felt full of joy."
    Loss(salad)              "There was the salad."       -> "The salad was lost."
    Warning(Mom, Lily, Tom)  "Mom warninged Tom."         -> "Mom warned Lily and Tom to be careful."
    Lesson(MatchesDanger)    "There was matchesdanger."   -> "It was an important lesson about matches danger."
    Friendship(Family)       "There was family."          -> "Everyone became good friends."
    Routine(Lily, play)      "Lily routined the play."    -> "Every day, Lily enjoyed play."
    catalyst=Help            "Something help happened."    -> "Help was on the way."
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Trace,
    NLGUtils,
    to_phrase,
    action_to_phrase,
    gerund_phrase,
    child_sentences,
    coherent,
    meta_story,
    is_meta_call,
    HappyEnd,
)

from gen6k03 import _split, _phrases, _kw_targets, _cap


def _names(chars):
    return NLGUtils.join_list([str(c) for c in chars])


def _be_past(subject: str) -> str:
    return "were" if subject.lower() == "they" else "was"


# ---------------------------------------------------------------------------
# Emotions / states (char-or-concept)
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Joy")
def JoyTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if chars:
        for c in chars:
            c.add_meme("Joy", 1.0)
        ctx.actor = chars[0]
        who = ctx.say(chars[0]) if len(chars) == 1 else _names(chars)
        return f"{who} felt full of joy."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"There was great joy over {thing}." if thing else "There was great joy."


@REGISTRY.kernel("Loss")
def LossTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if chars:
        owner = chars[0]
        owner.add_meme("Sadness", 0.5)
        ctx.actor = owner
        obj = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest))
        return f"{ctx.say(owner)} lost {obj} and felt sad." if obj else f"{ctx.say(owner)} felt a sense of loss."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"{_cap(thing)} was lost." if thing else "Something was lost."


# ---------------------------------------------------------------------------
# Communication
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Warning")
def WarningTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if chars:
        speaker = chars[0]
        ctx.actor = speaker
        listeners = NLGUtils.join_list([str(c) for c in chars[1:]] + _phrases(rest))
        return f"{ctx.say(speaker)} warned {listeners} to be careful." if listeners \
            else f"{ctx.say(speaker)} gave a warning."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"There was a warning about {thing}." if thing else "There was a warning."


@REGISTRY.kernel("Lesson")
def LessonTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else None
    # A short, reducible action Trace / plain concept goes into "a lesson about
    # <X>" as a gerund/noun ("warned everyone" -> "warning everyone"). Anything
    # that can't cleanly reduce (existential / multi-clause Compose trace) is
    # emitted as its own sentence so story beats aren't lost.
    about, extra = [], []
    for r in rest:
        g = gerund_phrase(r) if isinstance(r, Trace) else to_phrase(r)
        if g:
            about.append(g)
        else:
            cs = child_sentences(r)
            if cs:
                extra += cs
    topic = NLGUtils.join_list(about)
    if hero is not None:
        hero.add_meme("Wisdom", 1.0)
        ctx.actor = hero
        lead = (f"{ctx.say(hero)} learned a lesson about {topic}." if topic
                else f"{ctx.say(hero)} learned an important lesson that day.")
    else:
        lead = (f"It was an important lesson about {topic}." if topic
                else "It was an important lesson.")
    return coherent(ctx, hero, [lead] + extra)


# ---------------------------------------------------------------------------
# Social
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Friendship")
def FriendshipTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if len(chars) >= 2:
        for c in chars:
            c.add_meme("Friendship", 1.0)
        ctx.actor = chars[0]
        return f"{_names(chars)} became good friends."
    if chars:
        chars[0].add_meme("Friendship", 0.5)
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} made a good friend."
    return "Everyone became good friends."


@REGISTRY.kernel("Help")
def HelpTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if chars:
        helper = chars[0]
        ctx.actor = helper
        other = NLGUtils.join_list([str(c) for c in chars[1:]] + _phrases(rest) + _phrases(_kw_targets(kw)))
        return f"{ctx.say(helper)} helped {other}." if other else f"{ctx.say(helper)} helped out."
    target = NLGUtils.join_list(_phrases(rest) + _phrases(_kw_targets(kw)))
    return f"Someone helped with {target}." if target else "Help was on the way."


@REGISTRY.kernel("Hug")
def HugTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if len(chars) >= 2:
        chars[0].add_meme("Love", 0.5)
        ctx.actor = chars[0]
        return f"{chars[0]} gave {_names(chars[1:])} a big hug."
    if chars:
        chars[0].add_meme("Love", 0.3)
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} got a warm hug."
    return "There were warm hugs all around."


@REGISTRY.kernel("Share")
def ShareTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if chars:
        ctx.actor = chars[0]
        chars[0].add_meme("Love", 0.3)
        obj = NLGUtils.join_list(_phrases(rest))
        others = [str(c) for c in chars[1:]]
        if obj and others:
            return f"{chars[0]} shared {obj} with {NLGUtils.join_list(others)}."
        if obj:
            return f"{chars[0]} shared {obj}."
        if others:
            return f"{chars[0]} shared with {NLGUtils.join_list(others)}."
        return f"{ctx.say(chars[0])} shared with everyone."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"Everyone shared {thing}." if thing else "There was lots of sharing."


@REGISTRY.kernel("Give")
def GiveTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    if chars:
        giver = chars[0]
        ctx.actor = giver
        obj = NLGUtils.join_list(_phrases(rest))
        recips = [str(c) for c in chars[1:]]
        for c in chars[1:]:
            c.add_meme("Joy", 0.3)
        if obj and recips:
            return f"{giver} gave {obj} to {NLGUtils.join_list(recips)}."
        if obj:
            return f"{giver} gave {obj} away."
        if recips:
            return f"{giver} gave a gift to {NLGUtils.join_list(recips)}."
        return f"{ctx.say(giver)} gave it away."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"{_cap(thing)} was given away." if thing else "It was given as a gift."


# ---------------------------------------------------------------------------
# Object actions (need the protagonist when the character is implicit)
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Search")
def SearchTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    obj = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw)))
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} looked everywhere for {obj}." if obj else f"{ctx.say(actor)} searched all around."
    return f"Everyone searched for {obj}." if obj else "The search was on."


@REGISTRY.kernel("Return")
def ReturnTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    obj = NLGUtils.join_list(_phrases(rest))
    recips = [str(c) for c in chars[1:]]
    if actor is not None:
        ctx.actor = actor
        if obj and recips:
            return f"{ctx.say(actor)} returned {obj} to {NLGUtils.join_list(recips)}."
        if obj:
            return f"{ctx.say(actor)} returned {obj}."
        return f"{ctx.say(actor)} went back home."
    return "Everything was returned."


@REGISTRY.kernel("Brave")
def BraveTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None:
        had_fear = actor.Fear > 0.2
        actor.add_meme("Brave", 1.0)
        actor.add_meme("Fear", -0.35)
        ctx.actor = actor
        if had_fear:
            subj = actor.pronoun("subject")
            return f"Even though {ctx.say(actor)} was afraid, {subj} {_be_past(subj)} very brave."
        return f"{ctx.say(actor)} was very brave."
    return "It was a brave thing to do."


@REGISTRY.kernel("Bravery")
def BraveryTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    support = NLGUtils.join_list([str(c) for c in chars[1:]] + _phrases(rest) + _phrases(_kw_targets(kw)))
    if actor is not None:
        had_fear = actor.Fear > 0.2
        actor.add_meme("Brave", 1.0)
        actor.add_meme("Bravery", 1.0)
        actor.add_meme("Fear", -0.35)
        ctx.actor = actor
        if support:
            return f"{ctx.say(actor)} was brave for {support}."
        if had_fear:
            subj = actor.pronoun("subject")
            return f"Even though {ctx.say(actor)} was afraid, {subj} {_be_past(subj)} very brave."
        return f"{ctx.say(actor)} was very brave."
    return "being brave"


@REGISTRY.kernel("Altruism")
def AltruismTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None:
        actor.add_meme("Altruism", 1.0)
        actor.add_meme("Kindness", 0.5)
        actor.add_meme("Love", 0.2)
        ctx.actor = actor
        lead = f"{ctx.say(actor)} showed kindness by helping others."
        if is_meta_call(kw):
            body = meta_story(ctx, actor, kw)
            return coherent(ctx, actor, [lead] + ([body] if body else []))
        target = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw)))
        return f"{ctx.say(actor)} helped {target} with kindness." if target else lead
    target = NLGUtils.join_list(_phrases(rest) + _phrases(_kw_targets(kw)))
    return f"helping {target}" if target else "helping others"


@REGISTRY.kernel("Indifference")
def IndifferenceTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    target = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw)))
    if actor is not None:
        actor.add_meme("Indifference", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} did not seem to mind {target}." if target \
            else f"{ctx.say(actor)} did not seem to mind."
    return f"No one seemed to mind {target}." if target else "No one seemed to mind."


@REGISTRY.kernel("Satisfaction")
def SatisfactionTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    target = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw)))
    if actor is not None:
        actor.add_meme("Satisfaction", 1.0)
        actor.add_meme("Joy", 0.3)
        ctx.actor = actor
        subj = ctx.say(actor)
        return f"{subj} {_be_past(subj)} satisfied with {target}." if target \
            else f"{subj} felt satisfied."
    return f"There was satisfaction with {target}." if target else "There was satisfaction."


@REGISTRY.kernel("Reminder")
def ReminderTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    values = list(rest) + [v for v in kw.values() if v is not None]
    topic_parts = []
    for value in values:
        topic_parts.append(gerund_phrase(value) if isinstance(value, Trace) else to_phrase(value))
    topic = NLGUtils.join_list([p for p in topic_parts if p])
    if actor is not None:
        actor.add_meme("Reminder", 1.0)
        actor.add_meme("Wisdom", 0.2)
        ctx.actor = actor
        if len(chars) >= 2:
            listeners = _names(chars[1:])
            return f"{ctx.say(actor)} reminded {listeners} about {topic}." if topic \
                else f"{ctx.say(actor)} reminded {listeners}."
        return f"{ctx.say(actor)} remembered {topic}." if topic \
            else f"{ctx.say(actor)} remembered what mattered."
    return f"It was a reminder about {topic}." if topic else "It was a helpful reminder."


@REGISTRY.kernel("Clap")
def ClapTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actors = chars if chars else ([ctx.actor] if ctx.actor else [])
    target = NLGUtils.join_list(_phrases(rest) + _phrases(_kw_targets(kw)))
    if actors:
        for actor in actors:
            actor.add_meme("Joy", 0.2)
            actor.add_meme("Approval", 0.4)
        ctx.actor = actors[0]
        who = ctx.say(actors[0]) if len(actors) == 1 else _names(actors)
        return f"{who} clapped for {target}." if target else f"{who} clapped happily."
    return f"Everyone clapped for {target}." if target else "Everyone clapped happily."


@REGISTRY.kernel("HappyEnding")
def HappyEndingTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, _rest = _split(args)
    for char in chars:
        char.add_meme("Joy", 0.5)
    return HappyEnd(ctx)


# ---------------------------------------------------------------------------
# Structural concept-only fallbacks
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Conflict")
def ConflictConcept(ctx: World, *args: Any, **kw: Any) -> str:
    # Catches concept-only Conflict(NoFun); the Actor-based Conflict variants in
    # gen6k01 still win when a character (or current actor) is available.
    chars, rest = _split(args)
    over = NLGUtils.join_list(_phrases(rest))
    return f"There was a disagreement about {over}." if over else "There was a disagreement."


@REGISTRY.kernel("Routine")
def RoutineTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    sents = []
    concepts = []
    for r in rest:
        cs = child_sentences(r)
        if cs is not None:
            sents += cs
        else:
            p = to_phrase(r)
            if p:
                concepts.append(p)
    if actor is not None:
        ctx.actor = actor
        if sents:
            return coherent(ctx, actor, [f"Every day, {ctx.say(actor)} had the same routine."] + sents)
        if concepts:
            return f"Every day, {ctx.say(actor)} enjoyed {NLGUtils.join_list(concepts)}."
        return f"{ctx.say(actor)} went about the day as usual."
    if concepts:
        return f"Every day, there was {NLGUtils.join_list(concepts)}."
    return "Every day was much the same."


if __name__ == "__main__":
    import gen6registry  # noqa: F401
    from gen6 import generate

    tests = [
        "Lily(Character, girl)\nMom(Character, mother)\nJoy(Lily, Mom)",
        "Lily(Character, girl)\nLoss(salad)",
        "Mom(Character, mother)\nLily(Character, girl)\nTom(Character, boy)\nWarning(Mom, Lily, Tom)",
        "Lily(Character, girl)\nLesson(MatchesDanger)",
        "Lily(Character, girl)\nFriendship(Family)",
        "Lily(Character, girl)\nRoutine(Lily, play)",
        "Lily(Character, girl)\nQuest(Lily, catalyst=Help, outcome=Joy)",
        # Canonical shapes must stay unchanged:
        "Lily(Character, girl)\nJoy(Lily)",
        "Mom(Character, mother)\nLily(Character, girl)\nHelp(Mom, Lily)",
        "Lily(Character, girl)\nMom(Character, mother)\nGift(Character, doll)\nGive(Lily, doll, Mom)",
    ]
    for i, t in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(t))
        print()
