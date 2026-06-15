"""
gen6k01.py - Kernel Pack #01 for the gen6 engine.

Ports the highest-frequency kernels still missing from `gen6.py`, with an
emphasis on the **meta / structural** kernels that organize a whole story from
keyword phases (Quest, Journey, Cautionary, Conflict, Resolution, Encounter,
Accident, Transformation, Response). These consume already-evaluated kwarg
values (entities / concept strings / nested Traces) and render them with the
`*_to_phrase` helpers from gen6.

Plus a batch of simple actor(+object) action kernels (Eat, Drink, Ask, Climb,
Clean, Observe, Want, Discover, Request, Promise, Attempt, Rescue, Gift, Idea,
Realize, ...).

Authoring style (see AGENTS.md):
  - typed parameters (`Character`, `Physical`, `Actor`); multiple variants per
    name are fine - the dispatcher picks the best fit;
  - `ctx.say(subject)` renders the grammatical subject (pronoun-aware);
  - return a plain string (one or more sentences).
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Entity,
    Trace,
    Character,
    Physical,
    Actor,
    NLGUtils,
    to_phrase,
    state_to_phrase,
    action_to_phrase,
    event_to_phrase,
    infinitive_phrase,
    base_phrase,
    gerund_phrase,
    clause_inline,
    child_sentences,
    render_state,
    render_action,
    render_event,
    render_outcome,
    render_clause,
    coherent,
    meta_story,
    is_meta_call,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _refs(ctx: World, char: Entity):
    """Return (first_reference, subsequent_reference) for a subject.

    First mention uses the name (or pronoun if the coherence layer tagged this
    kernel); subsequent mentions within the same kernel use a pronoun to avoid
    repeating the name - the gen5 weakness this engine is meant to fix.
    """
    first = ctx.say(char)
    pron = char.pronoun("subject") if isinstance(char, Entity) and char.kind == "character" else first
    return first, pron


def _has(kw: dict, *keys: str):
    for k in keys:
        if k in kw and kw[k] is not None:
            return kw[k]
    return None


_ACTIONISH_PHYSICALS = {
    "act", "climb", "dance", "fly", "help", "jump", "listen", "play", "run",
    "pitch", "share", "swim", "talk", "tie", "walk", "work",
}


def _actionish_phrase(value: Any) -> str:
    if isinstance(value, Entity) and value.kind != "character":
        first = value.name.split(" ", 1)[0]
        if value.name in _ACTIONISH_PHYSICALS or first in _ACTIONISH_PHYSICALS:
            return value.name
    return base_phrase(value)


# ---------------------------------------------------------------------------
# Meta / structural kernels (keyword phases)
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Quest")
@REGISTRY.kernel("Journey")
def Quest(ctx: World, hero: Actor, goal: Any = None, **kw: Any) -> str:
    """Hero pursues a goal through phases: state/catalyst/process/insight/outcome.

    Phase rendering and pronoun coherence are delegated to the shared
    ``meta_story`` builder (gen6); child kernels in each phase are emitted as
    their own sentences and repeated subjects collapse to pronouns.
    """
    hero.Quest += 1
    ctx.actor = hero
    if goal is not None and "goal" not in kw:
        kw = dict(kw, goal=goal)
    return meta_story(ctx, hero, kw, fallback=f"{hero.name} went on a great adventure.")


@REGISTRY.kernel("Friendship")
def FriendshipMeta(ctx: World, a: Actor, b: Character, **kw: Any) -> str:
    """Friendship with optional narrative phases (state/catalyst/process/outcome)."""
    a.Friendship += b
    ctx.actor = a
    sents = []
    state = _has(kw, "state")
    if state is not None:
        sents += render_state(a.name, state)
    catalyst = _has(kw, "catalyst", "trigger")
    if catalyst is not None:
        sents += render_event(catalyst)
    process = _has(kw, "process", "action")
    if process is not None:
        cs = child_sentences(process)
        sents += cs if cs is not None else [f"{a.name} and {b} {action_to_phrase(process)}."]
    sents.append(f"Together, {a.name} and {b} became good friends.")
    outcome = _has(kw, "outcome", "result")
    if outcome is not None:
        sents += render_outcome("", outcome)
    return coherent(ctx, a, sents)


@REGISTRY.kernel("Cautionary")
def Cautionary(ctx: World, char: Actor, **kw: Any) -> str:
    """A mistake leads to a consequence and a lesson."""
    ctx.actor = char
    if is_meta_call(kw):
        body = meta_story(ctx, char, kw)
        if body:
            char.Wisdom += 1
            return body
    sents = []
    state = _has(kw, "state")
    if state is not None:
        sents += render_state(char.name, state)
    mistake = _has(kw, "mistake", "action", "flaw", "behavior")
    if mistake is not None:
        sents += render_action(char.name, mistake)
    consequence = _has(kw, "consequence", "result", "outcome")
    if consequence is not None:
        sents += render_clause(consequence, "Because of that, {}.")
    lesson = _has(kw, "lesson", "insight", "moral")
    if lesson is not None:
        char.Wisdom += 1
        cs = child_sentences(lesson)
        sents += cs if cs is not None else [f"{char.name} learned that {to_phrase(lesson)}."]
    if not sents:
        sents.append(f"{char.name} learned an important lesson.")
    return coherent(ctx, char, sents)


@REGISTRY.kernel("Encounter")
def Encounter(ctx: World, char: Actor, other: Character, **kw: Any) -> str:
    ctx.actor = char
    name, _ = _refs(ctx, char)
    place = _has(kw, "place", "setting", "location")
    where = f" near {to_phrase(place)}" if place is not None else ""
    line = f"{name} came across {other}{where}."
    state = _has(kw, "state", "mood")
    if state is not None:
        line += f" {other} seemed {state_to_phrase(state)}."
    return line


@REGISTRY.kernel("Encounter")
def EncounterObject(ctx: World, char: Actor, thing: Physical, **kw: Any) -> str:
    ctx.actor = char
    ctx.current_object = thing
    name, _ = _refs(ctx, char)
    place = _has(kw, "place", "setting", "location")
    where = f" near {to_phrase(place)}" if place is not None else ""
    return f"{name} came across {thing}{where}."


@REGISTRY.kernel("Accident")
def Accident(ctx: World, char: Actor, **kw: Any) -> str:
    ctx.actor = char
    name, _ = _refs(ctx, char)
    action = _has(kw, "action", "cause")
    result = _has(kw, "result", "consequence", "outcome")
    sents = ["Suddenly, something went wrong."]
    if action is not None:
        cs = child_sentences(action)
        if cs is not None:
            sents = cs
        elif isinstance(action, Entity) and action.kind != "character":
            sents = [f"{name} had an accident with {to_phrase(action)}."]
        else:
            sents = [f"{name} accidentally {action_to_phrase(action)}."]
    if result is not None:
        sents += render_clause(result, "As a result, {}.")
    char.Surprise += 1
    return coherent(ctx, char, sents)


@REGISTRY.kernel("Conflict")
def Conflict(ctx: World, a: Actor, b: Character = None, **kw: Any) -> str:
    ctx.actor = a
    over = _has(kw, "over", "about", "cause")
    if b is not None:
        line = f"{ctx.say(a)} and {b} did not agree"
    else:
        line = f"{ctx.say(a)} had a problem"
    line += f" about {to_phrase(over)}." if over is not None else "."
    a.Anger += 0.5
    sents = [line]
    res = _has(kw, "resolution", "outcome")
    if res is not None:
        sents += render_clause(res, "In the end, {}.")
    return coherent(ctx, a, sents)


@REGISTRY.kernel("Resolution")
@REGISTRY.kernel("Response")
def Resolution(ctx: World, char: Actor = None, **kw: Any) -> str:
    bits = []
    process = _has(kw, "process", "action")
    if process is not None:
        cs = child_sentences(process)
        if cs is not None:
            bits += cs
        else:
            subj = char.name if char is not None else "They"
            bits.append(f"{subj} {action_to_phrase(process)}.")
    outcome = _has(kw, "outcome", "result", "emotion")
    if outcome is not None:
        cs = child_sentences(outcome)
        bits += cs if cs is not None else [f"In the end, everything was {state_to_phrase(outcome)}."]
    if not bits:
        bits.append("In the end, everything worked out.")
    return coherent(ctx, char, bits)


@REGISTRY.kernel("Transformation")
def Transformation(ctx: World, char: Actor, change: Any = None, **kw: Any) -> str:
    ctx.actor = char
    char.Joy += 0.5
    pieces = [change] + list(kw.values())
    trace_texts = []
    concept_texts = []
    for p in pieces:
        if p is None:
            continue
        if isinstance(p, Trace):
            if p.text.strip():
                trace_texts.append(p.text.strip())
        else:
            t = state_to_phrase(p)
            if t:
                concept_texts.append(t)
    out = []
    if concept_texts:
        out.append(f"In the end, {ctx.say(char)} was {NLGUtils.join_list(concept_texts)}.")
    for tt in trace_texts:
        out.append(tt if tt.endswith((".", "!", "?")) else tt + ".")
    if not out:
        out.append(f"{ctx.say(char)} was changed forever.")
    return " ".join(out)


# ---------------------------------------------------------------------------
# Desire / cognition
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Desire")
@REGISTRY.kernel("Want")
@REGISTRY.kernel("Longing")
def Desire(ctx: World, char: Actor, thing: Any = None, **kw: Any) -> str:
    char.Desire += 1
    ctx.actor = char
    obj = thing if thing is not None else _has(kw, "goal", "object")
    if obj is not None:
        # An action goal reads as an infinitive ("wanted to climb the tree"); a
        # plain object stays a noun ("wanted the ball"). An un-reducible action
        # clause yields "" -> fall through to the generic wish line.
        want = infinitive_phrase(obj)
        if want:
            return f"{ctx.say(char)} really wanted {want}."
    return f"{ctx.say(char)} wished for something special."


@REGISTRY.kernel("Longing")
def LongingConcept(ctx: World, thing: Physical) -> str:
    return f"a longing for {thing}"


@REGISTRY.kernel("Idea")
@REGISTRY.kernel("Decision")
@REGISTRY.kernel("Plan")
def Idea(ctx: World, char: Actor, **kw: Any) -> str:
    char.Joy += 0.2
    ctx.actor = char
    helps = _has(kw, "help", "goal", "to")
    if helps is not None:
        return f"{ctx.say(char)} had an idea to help {to_phrase(helps)}."
    return f"{ctx.say(char)} had a clever idea."


@REGISTRY.kernel("Realization")
@REGISTRY.kernel("Insight")
@REGISTRY.kernel("Realize")
def Insight(ctx: World, char: Actor, what: Any = None, **kw: Any) -> str:
    char.Wisdom += 1
    ctx.actor = char
    w = what if what is not None else _has(kw, "lesson", "that")
    if w is not None:
        # Keep an embedded clause's subject but lower-case it so it reads as a
        # subordinate clause ("realized that help was on the way").
        return f"{ctx.say(char)} realized that {clause_inline(w)}."
    return f"{ctx.say(char)} suddenly understood."


@REGISTRY.kernel("Wonder")
@REGISTRY.kernel("Curiosity")
def Wonder(ctx: World, char: Actor, about: Any = None, **kw: Any) -> str:
    ctx.actor = char
    a = about if about is not None else _has(kw, "about")
    if a is not None:
        return f"{ctx.say(char)} wondered about {to_phrase(a)}."
    return f"{ctx.say(char)} was very curious."


# ---------------------------------------------------------------------------
# Discovery / perception
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Discovery")
@REGISTRY.kernel("Discover")
def Discovery(ctx: World, char: Actor, thing: Physical = None, **kw: Any) -> str:
    char.Joy += 0.4
    ctx.actor = char
    if thing is not None:
        ctx.current_object = thing
        return f"{ctx.say(char)} discovered {thing}."
    obj = _has(kw, "object", "what")
    if obj is not None:
        return f"{ctx.say(char)} discovered {to_phrase(obj)}."
    return f"{ctx.say(char)} made a wonderful discovery."


@REGISTRY.kernel("Observe")
@REGISTRY.kernel("Look")
@REGISTRY.kernel("Watch")
def Observe(ctx: World, char: Actor, thing: Physical = None, **kw: Any) -> str:
    ctx.actor = char
    lead = ctx.mood_lead(char)  # state-aware flavor (e.g. "nervously looked at")
    if thing is not None:
        ctx.current_object = thing
        return f"{ctx.say(char)} {lead}looked at {thing}."
    return f"{ctx.say(char)} {lead}looked around carefully."


# ---------------------------------------------------------------------------
# Communication
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Ask")
@REGISTRY.kernel("Request")
def Ask(ctx: World, asker: Actor, other: Character = None, **kw: Any) -> str:
    ctx.actor = asker
    what = _has(kw, "for", "about", "request", "help")
    if other is not None and what is not None:
        return f"{ctx.say(asker)} asked {other} for {to_phrase(what)}."
    if other is not None:
        return f"{ctx.say(asker)} asked {other} a question."
    if what is not None:
        return f"{ctx.say(asker)} asked for {to_phrase(what)}."
    return f"{ctx.say(asker)} asked a question."


@REGISTRY.kernel("Promise")
def Promise(ctx: World, char: Actor, other: Character = None, **kw: Any) -> str:
    char.Love += 0.2
    ctx.actor = char
    what = _has(kw, "to", "that")
    tail = f" to {to_phrase(what)}" if what is not None else ""
    if other is not None:
        return f"{ctx.say(char)} promised {other}{tail}."
    return f"{ctx.say(char)} made a promise{tail}."


@REGISTRY.kernel("Encourage")
def Encourage(ctx: World, char: Actor, other: Character, **kw: Any) -> str:
    char.Love += 0.2
    other.Joy += 0.4
    ctx.actor = char
    return f"{ctx.say(char)} encouraged {other}."


# ---------------------------------------------------------------------------
# Physical actions
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Eat")
def Eat(ctx: World, char: Actor, food: Physical = None, **kw: Any) -> str:
    ctx.actor = char
    lead = ctx.mood_lead(char)  # reflect prior state before Eat's own Joy bump
    char.Joy += 0.2
    if food is not None:
        return f"{ctx.say(char)} {lead}ate {food}."
    return f"{ctx.say(char)} {lead}had something to eat."


@REGISTRY.kernel("Drink")
def Drink(ctx: World, char: Actor, drink: Physical = None, **kw: Any) -> str:
    ctx.actor = char
    if drink is not None:
        return f"{ctx.say(char)} drank {drink}."
    return f"{ctx.say(char)} had a drink."


@REGISTRY.kernel("Climb")
def Climb(ctx: World, char: Actor, thing: Physical = None, **kw: Any) -> str:
    ctx.actor = char
    lead = ctx.mood_lead(char)
    if thing is not None:
        return f"{ctx.say(char)} {lead}climbed {thing}."
    return f"{ctx.say(char)} {lead}climbed up high."


@REGISTRY.kernel("Clean")
@REGISTRY.kernel("Wash")
def Clean(ctx: World, char: Actor, thing: Physical = None, **kw: Any) -> str:
    char.Pride += 0.2
    ctx.actor = char
    if thing is not None:
        return f"{ctx.say(char)} cleaned {thing}."
    return f"{ctx.say(char)} tidied everything up."


@REGISTRY.kernel("Drop")
def Drop(ctx: World, char: Actor, thing: Physical, **kw: Any) -> str:
    ctx.actor = char
    ctx.current_object = thing
    return f"{ctx.say(char)} dropped {thing}."


@REGISTRY.kernel("Spill")
def Spill(ctx: World, liquid: Physical, surface: Physical = None, **kw: Any) -> str:
    where = f" on {surface}" if surface is not None else ""
    return f"{str(liquid).capitalize()} spilled{where}."


@REGISTRY.kernel("Throw")
def Throw(ctx: World, char: Actor, thing: Physical = None, **kw: Any) -> str:
    ctx.actor = char
    if thing is not None:
        return f"{ctx.say(char)} threw {thing} away."
    return f"{ctx.say(char)} threw it away."


# ---------------------------------------------------------------------------
# Rescue / care / outcomes
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Rescue")
@REGISTRY.kernel("Save")
def Rescue(ctx: World, hero: Actor, victim: Character = None, **kw: Any) -> str:
    hero.Brave += 1
    ctx.actor = hero
    if is_meta_call(kw):
        body = meta_story(ctx, hero, kw)
        intro = f"{ctx.say(hero)} tried to help."
        if victim is not None:
            victim.Relief += 0.6
            intro = f"{ctx.say(hero)} tried to rescue {victim}."
        return coherent(ctx, hero, [intro] + ([body] if body else []))
    if victim is not None:
        victim.Relief += 0.6
        return f"{ctx.say(hero)} bravely rescued {victim}."
    obj = _has(kw, "object", "what")
    if obj is not None:
        return f"{ctx.say(hero)} saved {to_phrase(obj)}."
    return f"{ctx.say(hero)} saved the day."


@REGISTRY.kernel("Gift")
@REGISTRY.kernel("Giving")
def Gift(ctx: World, giver: Actor, thing: Physical = None, receiver: Character = None, **kw: Any) -> str:
    ctx.actor = giver
    if receiver is not None:
        receiver.Joy += 0.5
    obj = thing if thing is not None else _has(kw, "object")
    if obj is not None and receiver is not None:
        return f"{ctx.say(giver)} gave {to_phrase(obj)} to {receiver} as a gift."
    if obj is not None:
        return f"{ctx.say(giver)} gave a gift of {to_phrase(obj)}."
    return f"{ctx.say(giver)} gave a thoughtful gift."


@REGISTRY.kernel("Success")
@REGISTRY.kernel("Restoration")
def Success(ctx: World, char: Actor = None, thing: Physical = None, **kw: Any) -> str:
    if char is not None:
        char.Joy += 0.6
        what = thing if thing is not None else _has(kw, "object", "what")
        if what is not None:
            return f"{ctx.say(char)} succeeded with {to_phrase(what)}."
        return f"{ctx.say(char)} succeeded at last."
    if thing is not None:
        if isinstance(thing, Entity) and thing.kind != "character" and thing.name in _ACTIONISH_PHYSICALS:
            return "It worked at last."
        return f"{str(thing).capitalize()} was as good as new."
    return "Everything was put right again."


@REGISTRY.kernel("Attempt")
@REGISTRY.kernel("Try")
def Attempt(ctx: World, char: Actor, what: Any = None, **kw: Any) -> str:
    ctx.actor = char
    w = what if what is not None else _has(kw, "goal", "action", "process")
    if w is not None:
        # "tried to <base verb>": base_phrase keeps a concept verb in base form
        # ("fly", not "flapped"->"flap") and reduces an action Trace.
        b = _actionish_phrase(w)
        if b:
            return f"{ctx.say(char)} tried to {b}."
    aid = _has(kw, "aid", "help")
    if aid is not None:
        return f"{ctx.say(char)} tried hard, with help from {to_phrase(aid)}."
    return f"{ctx.say(char)} gave it a try."


@REGISTRY.kernel("Moral")
def Moral(ctx: World, lesson: Any = None, **kw: Any) -> str:
    text = lesson if lesson is not None else _has(kw, "lesson")
    if text is not None:
        if isinstance(text, str):
            return f"The moral of the story is to {base_phrase(text)}."
        topic = gerund_phrase(text) if isinstance(text, Trace) else to_phrase(text)
        return f"The moral of the story is about {topic}." if topic \
            else "And that was the moral of the story."
    return "And that was the moral of the story."


# ---------------------------------------------------------------------------
# State kernels (subject becomes adjective)
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Routine")
def Routine(ctx: World, char: Actor = None, **kw: Any) -> str:
    if char is None:
        return "Every day was much the same."
    ctx.actor = char
    act = _has(kw, "activity", "action")
    if act is not None:
        return f"Every day, {ctx.say(char)} {action_to_phrase(act)}."
    if is_meta_call(kw):
        body = meta_story(ctx, char, kw)
        if body:
            return coherent(ctx, char, [f"Every day, {ctx.say(char)} had a routine."] + [body])
    return f"{ctx.say(char)} went about the day as usual."


@REGISTRY.kernel("Lonely")
def Lonely(ctx: World, char: Actor) -> str:
    char.Sadness += 0.5
    return f"{ctx.say(char)} felt a little lonely."


@REGISTRY.kernel("Excited")
def Excited(ctx: World, char: Actor) -> str:
    char.Joy += 0.6
    return f"{ctx.say(char)} was very excited."


@REGISTRY.kernel("Fun")
@REGISTRY.kernel("Social")
@REGISTRY.kernel("Friendship")
def FunConcept(ctx: World) -> str:
    # Zero-arg concept fallbacks so bare `Fun` / `Social` read cleanly.
    return "There was lots of fun."


if __name__ == "__main__":
    import gen6registry  # noqa: F401  (load sibling packs so cross-pack kernels resolve)
    from gen6 import generate

    tests = [
        """Bobo(Character, dog, Clumsy + Playful)
Quest(Bobo,
    state = Routine + Longing(ball),
    catalyst = Surprise(ball),
    process = Chase(ball) + Find(newPlace) + Play(smallball),
    insight = Friendship + Fun,
    transformation = Happy + Social)""",
        """Sam(Character, fireman, Kind + Sharing)
Lily(Character, girl, Sad)
Encounter(Sam, Lily, place=tree, state=Sad)
Idea(Sam, help=Lily)
Share(Sam, Lily, firetruck)
Play(Sam, Lily)
Transformation(Lily, Happy)
Friendship(Sam, Lily)""",
    ]
    for i, t in enumerate(tests, 1):
        print(f"--- STORY {i} ---")
        print(generate(t))
        print()
