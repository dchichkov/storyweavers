'''Bounded, deterministic library adventure using atomic local plays.'''
from copy import deepcopy
from dataclasses import asdict, dataclass
import argparse
import json
import random
from pathlib import Path

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


SPOTS = ('returns_cart', 'low_shelf', 'top_shelf', 'window_nook')
SCENES = (
    'promise', 'catalog', 'librarian', 'returns_search', 'low_search',
    'ladder_search', 'bookmark_vignette', 'window_vignette',
    'friend_vignette', 'shelf_vignette', 'ending_found', 'ending_miss',
)
ENDINGS = {'ending_found', 'ending_miss'}


@dataclass(frozen=True, kw_only=True)
class Parameters:
    closing_minutes: int = 12
    book_location: str = 'returns_cart'
    catalog_current: bool = True
    ladder_stable: bool = True
    staff_available: bool = True
    trolley_wheel_ok: bool = True

    def __post_init__(self):
        if type(self.closing_minutes) is not int or not 7 <= self.closing_minutes <= 16:
            raise ValueError('closing_minutes must be an integer from 7 through 16')
        if type(self.book_location) is not str or self.book_location not in SPOTS:
            raise ValueError(f'book_location must be one of {SPOTS}')
        for name in ('catalog_current', 'ladder_stable', 'staff_available', 'trolley_wheel_ok'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be a bool')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        closing_minutes=rng.choice((8, 10, 12, 14)),
        book_location=rng.choice(SPOTS),
        catalog_current=rng.choice((True, False)),
        ladder_stable=rng.choice((True, False)),
        staff_available=rng.choice((True, False)),
        trolley_wheel_ok=rng.choice((True, False)),
    )


def _make_initial(p):
    return {
        'story.ended': False, 'story.outcome': '',
        'promise.status': 'none',
        'clock.minute': 0, 'library.closes_at': p.closing_minutes, 'library.closed': False,
        'param.closing_minutes': p.closing_minutes, 'param.book_location': p.book_location,
        'param.catalog_current': p.catalog_current, 'param.ladder_stable': p.ladder_stable,
        'param.staff_available': p.staff_available, 'param.trolley_wheel_ok': p.trolley_wheel_ok,
        'book.actual_spot': p.book_location, 'book.location': p.book_location,
        'book.found': False, 'book.title': 'The Moon in My Pocket', 'book.borrower': 'Nia',
        'friend.title_named': False, 'friend.trust': 0,
        'friend.bookmark_vignette': False, 'friend.window_vignette': False,
        'friend.agency_vignette': False, 'friend.helping': False,
        'friend.shelf_vignette': False, 'friend.shelf_skill': False,
        'friend.substitute_book': '', 'bookmark.location': 'Nia',
        'catalog.checked': False, 'catalog.lead': '',
        'staff.checked': False, 'staff.hint': '', 'staff.ladder_safe': False,
        'trolley.owner': 'library', 'trolley.location': 'return_bay',
        'trolley.useful': False, 'trolley.sorted_returns': False,
        'trolley.wheel_ok': p.trolley_wheel_ok,
        'search.returns_done': False, 'search.low_done': False,
        'search.ladder_done': False, 'search.window_done': False, 'search.count': 0,
    }


_DEFAULT_STATE = _make_initial(Parameters())


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    return deepcopy(_make_initial(params))


def validate(state):
    if not isinstance(state, dict):
        raise StoryError('State must be a dictionary')
    if set(state) != set(_DEFAULT_STATE):
        missing = set(_DEFAULT_STATE) - set(state)
        extra = set(state) - set(_DEFAULT_STATE)
        raise StoryError(f'Wrong state keys; missing={sorted(missing)}, extra={sorted(extra)}')
    for key, default in _DEFAULT_STATE.items():
        if type(state[key]) is not type(default):
            raise StoryError(f'Wrong type for {key}')
    if state['book.actual_spot'] not in SPOTS or state['param.book_location'] not in SPOTS:
        raise StoryError('Unknown book location')
    if state['param.closing_minutes'] != state['library.closes_at']:
        raise StoryError('Closing parameter and library clock disagree')
    if not 7 <= state['library.closes_at'] <= 16:
        raise StoryError('Closing time is outside the supported range')
    if state['book.actual_spot'] != state['param.book_location']:
        raise StoryError('The book’s physical spot cannot change')
    if state['catalog.lead'] not in ('', *SPOTS):
        raise StoryError('Unknown catalogue lead')
    if state['catalog.checked'] != bool(state['catalog.lead']):
        raise StoryError('Catalogue check and lead disagree')
    if state['staff.hint'] not in ('', 'none', *SPOTS):
        raise StoryError('Unknown staff hint')
    if not state['staff.checked'] and (state['staff.hint'] or state['staff.ladder_safe']):
        raise StoryError('Unasked staff cannot provide a hint or ladder clearance')
    if state['staff.ladder_safe'] and not (
        state['staff.checked'] and state['param.staff_available'] and state['param.ladder_stable']
    ):
        raise StoryError('Ladder clearance requires available staff and a stable ladder')
    if state['trolley.wheel_ok'] != state['param.trolley_wheel_ok']:
        raise StoryError('Trolley wheel parameter changed')
    if state['clock.minute'] < 0 or state['clock.minute'] > state['library.closes_at']:
        raise StoryError('Clock is outside library hours')
    if state['library.closed'] != (state['clock.minute'] >= state['library.closes_at']):
        raise StoryError('Closing bell and clock disagree')
    status = state['promise.status']
    if status not in ('none', 'made', 'kept', 'honest'):
        raise StoryError('Unknown promise status')
    if state['friend.title_named'] != (status != 'none'):
        raise StoryError('The promise and named title disagree')
    if status == 'none':
        if state['trolley.owner'] != 'library' or state['trolley.location'] != 'return_bay':
            raise StoryError('The trolley cannot be borrowed before the promise scene')
        if state['trolley.useful'] or state['trolley.sorted_returns']:
            raise StoryError('Unused trolley has invented effects')
    if state['trolley.owner'] == 'Lio':
        if state['trolley.location'] != 'with_Lio' or not state['trolley.useful']:
            raise StoryError('Borrowed trolley location or use is inconsistent')
        if status == 'none':
            raise StoryError('Trolley has no borrower')
    elif state['trolley.owner'] == 'library':
        if state['trolley.location'] != 'return_bay':
            raise StoryError('Library-owned trolley must be in its bay')
    else:
        raise StoryError('Unknown trolley owner')
    if state['trolley.sorted_returns'] != state['trolley.useful']:
        raise StoryError('Trolley usefulness must come from the enacted clearing action')
    if not state['friend.agency_vignette'] and state['friend.helping']:
        raise StoryError('Nia cannot help through an omitted vignette')
    if state['friend.agency_vignette'] != state['friend.helping']:
        raise StoryError('Nia’s help and vignette disagree')
    if state['friend.shelf_vignette'] != state['friend.shelf_skill']:
        raise StoryError('Shelf knowledge must come from its vignette')
    if state['friend.window_vignette'] != state['search.window_done']:
        raise StoryError('Window encounter and search flag disagree')
    if state['friend.bookmark_vignette']:
        if state['bookmark.location'] not in ('Lio', 'book', 'Nia'):
            raise StoryError('Shared bookmark has an impossible location')
    elif state['bookmark.location'] != 'Nia':
        raise StoryError('Unshared bookmark changed custody')
    if state['bookmark.location'] == 'Lio' and not state['friend.bookmark_vignette']:
        raise StoryError('Lio cannot hold an unshared bookmark')
    if state['bookmark.location'] == 'book' and not state['book.found']:
        raise StoryError('Bookmark cannot be inside a book that was not found')
    if state['search.count'] < 0 or state['search.count'] > 4:
        raise StoryError('Invalid number of searches')
    minimum_searches = sum(state[k] for k in ('search.returns_done', 'search.low_done', 'search.ladder_done'))
    maximum_searches = minimum_searches + int(state['search.window_done'])
    if not minimum_searches <= state['search.count'] <= maximum_searches:
        raise StoryError('Search count and enacted search flags disagree')
    if state['book.found']:
        if status == 'none' or state['book.location'] not in ('trolley', 'Nia'):
            raise StoryError('Found book has an impossible location')
        if status == 'kept' and state['book.location'] != 'Nia':
            raise StoryError('Kept promise requires the book in Nia’s hands')
        if status != 'kept' and state['book.location'] != 'trolley':
            raise StoryError('A recovered book stays on the trolley until handoff')
    elif state['book.location'] != state['book.actual_spot']:
        raise StoryError('Unfound book moved without a discovery')
    if status == 'kept' and not state['book.found']:
        raise StoryError('A promise cannot be kept without the book')
    if status == 'honest' and (state['book.found'] or not state['friend.substitute_book']):
        raise StoryError('Honest failure requires an unfound book and an enacted substitute')
    if status not in ('honest',) and state['friend.substitute_book']:
        raise StoryError('Substitute book appeared without the failure choice')
    if state['story.ended']:
        if state['trolley.owner'] != 'library' or state['trolley.location'] != 'return_bay' or not state['trolley.useful']:
            raise StoryError('An ending must return the useful trolley')
        if status == 'kept':
            if state['story.outcome'] != 'promise_kept' or not state['book.found'] or state['library.closed']:
                raise StoryError('Success must hand over the book before closing')
        elif status == 'honest':
            if state['story.outcome'] != 'promise_not_kept_honestly' or state['book.found']:
                raise StoryError('Failure ending contradicts the search')
        else:
            raise StoryError('Story ended without resolving the promise')
    elif state['story.outcome']:
        raise StoryError('An unfinished story cannot have an outcome')
    if state['promise.status'] == 'kept' and state['bookmark.location'] == 'book' and not state['friend.bookmark_vignette']:
        raise StoryError('Unshared bookmark cannot enter the recovered book')


def _params_match(params, state):
    values = asdict(params)
    for name, value in values.items():
        if state[f'param.{name}'] != value:
            raise StoryError(f'Parameters do not match state: {name}')


def _low_allowed(state):
    return (
        state['catalog.lead'] == 'low_shelf'
        or state['staff.hint'] == 'low_shelf'
        or state['friend.shelf_skill']
    )


def _ladder_allowed(state):
    return (
        not state['library.closed'] and not state['book.found']
        and not state['search.ladder_done'] and state['staff.checked']
        and state['staff.ladder_safe'] and state['catalog.checked']
        and (state['catalog.lead'] == 'top_shelf' or state['staff.hint'] == 'top_shelf')
    )


def _remaining_searches(state):
    if state['library.closed'] or state['book.found']:
        return []
    remaining = []
    if not state['search.returns_done']:
        remaining.append('returns_cart')
    if not state['search.low_done'] and _low_allowed(state):
        remaining.append('low_shelf')
    if not state['search.window_done']:
        remaining.append('window_nook')
    if not state['search.ladder_done'] and state['param.staff_available'] and state['param.ladder_stable']:
        if not state['staff.checked'] or (
            state['staff.ladder_safe'] and (
                state['catalog.lead'] == 'top_shelf' or state['staff.hint'] == 'top_shelf'
            )
        ):
            remaining.append('top_shelf')
    return remaining


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'promise':
        return state['promise.status'] == 'none'
    if state['promise.status'] == 'none':
        return False
    if scene_id == 'catalog':
        return not state['catalog.checked'] and not state['library.closed']
    if scene_id == 'librarian':
        return not state['staff.checked']
    if scene_id == 'returns_search':
        return state['catalog.checked'] and not state['book.found'] and not state['library.closed'] and not state['search.returns_done']
    if scene_id == 'low_search':
        return state['catalog.checked'] and not state['book.found'] and not state['library.closed'] and not state['search.low_done'] and _low_allowed(state)
    if scene_id == 'ladder_search':
        return _ladder_allowed(state)
    if scene_id == 'bookmark_vignette':
        return not state['friend.bookmark_vignette']
    if scene_id == 'window_vignette':
        return state['catalog.checked'] and not state['friend.window_vignette']
    if scene_id == 'friend_vignette':
        return not state['friend.agency_vignette']
    if scene_id == 'shelf_vignette':
        return not state['friend.shelf_vignette']
    if scene_id == 'ending_found':
        return state['catalog.checked'] and state['book.found'] and not state['library.closed']
    if scene_id == 'ending_miss':
        return state['catalog.checked'] and not state['book.found'] and (
            state['library.closed'] or (state['search.count'] > 0 and not _remaining_searches(state))
        )
    return False


def _timed(changes, state, cost):
    result = dict(changes)
    minute = state['clock.minute'] + cost
    result['clock.minute'] = minute
    result['library.closed'] = minute >= state['library.closes_at']
    return result


def _find_if_here(play, spot):
    state = play.state
    if state['book.actual_spot'] == spot and not state['library.closed'] and not state['book.found']:
        play.act(
            f'find_book_at_{spot}',
            requires={'book.found': False, 'book.actual_spot': spot, 'library.closed': False},
            **{'book.found': True, 'book.location': 'trolley'},
        )


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    validate(state)
    _params_match(params, state)
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('Lio', 'Nia', 'Ms Vale'), validate=validate)
    if scene_id == 'promise':
        play.act(
            'listen_to_nia_name_the_missing_book',
            requires={'promise.status': 'none', 'friend.title_named': False},
            **{'promise.status': 'made', 'friend.title_named': True, 'friend.trust': 1},
        )
        play.act(
            'borrow_trolley_and_clear_the_aisle',
            requires={'promise.status': 'made', 'trolley.owner': 'library'},
            **{'trolley.owner': 'Lio', 'trolley.location': 'with_Lio', 'trolley.useful': True, 'trolley.sorted_returns': True},
        )
    elif scene_id == 'catalog':
        spot = play.state['book.actual_spot'] if play.state['param.catalog_current'] else 'low_shelf'
        play.act(
            'check_catalogue_entry',
            requires={'friend.title_named': True, 'catalog.checked': False, 'library.closed': False},
            **_timed({'catalog.checked': True, 'catalog.lead': spot}, play.state, 1),
        )
    elif scene_id == 'librarian':
        before = play.state
        available = before['param.staff_available'] and not before['library.closed']
        hint = before['book.actual_spot'] if available else 'none'
        safe = bool(available and before['param.ladder_stable'])
        changes = {'staff.checked': True, 'staff.hint': hint, 'staff.ladder_safe': safe}
        if not before['book.found'] and not before['library.closed']:
            changes = _timed(changes, before, 1)
        play.act('ask_ms_vale_for_a_search_clue_and_safe_help', requires={'staff.checked': False}, **changes)
    elif scene_id == 'returns_search':
        before = play.state
        cost = 1 if before['trolley.wheel_ok'] else 2
        changes = {
            'search.returns_done': True, 'search.count': before['search.count'] + 1,
            'trolley.sorted_returns': True,
        }
        play.act(
            'sort_the_returns_on_the_borrowed_trolley',
            requires={'catalog.checked': True, 'book.found': False, 'library.closed': False,
                      'search.returns_done': False, 'trolley.owner': 'Lio'},
            **_timed(changes, before, cost),
        )
        _find_if_here(play, 'returns_cart')
    elif scene_id == 'low_search':
        before = play.state
        play.act(
            'check_the_low_picture_book_shelf',
            requires={'catalog.checked': True, 'book.found': False, 'library.closed': False,
                      'search.low_done': False},
            **_timed({'search.low_done': True, 'search.count': before['search.count'] + 1}, before, 1),
        )
        _find_if_here(play, 'low_shelf')
    elif scene_id == 'ladder_search':
        before = play.state
        play.act(
            'search_the_staff_checked_upper_shelf',
            requires={'staff.checked': True, 'staff.ladder_safe': True, 'book.found': False,
                      'library.closed': False, 'search.ladder_done': False},
            **_timed({'search.ladder_done': True, 'search.count': before['search.count'] + 1}, before, 1),
        )
        _find_if_here(play, 'top_shelf')
    elif scene_id == 'bookmark_vignette':
        before = play.state
        play.act(
            'let_lio_hold_nias_moon_bookmark',
            requires={'friend.bookmark_vignette': False, 'bookmark.location': 'Nia'},
            **{'friend.bookmark_vignette': True, 'bookmark.location': 'Lio', 'friend.trust': before['friend.trust'] + 1},
        )
    elif scene_id == 'window_vignette':
        before = play.state
        changes = {
            'search.window_done': True, 'friend.window_vignette': True,
            'friend.trust': before['friend.trust'] + 1,
        }
        if not before['book.found'] and not before['library.closed']:
            changes['search.count'] = before['search.count'] + 1
            play.act(
                'check_the_window_seat_with_nia',
                requires={'catalog.checked': True, 'search.window_done': False,
                          'book.found': False, 'library.closed': False},
                **_timed(changes, before, 1),
            )
            _find_if_here(play, 'window_nook')
        else:
            play.act(
                'share_a_window_memory_before_leaving',
                requires={'search.window_done': False},
                **changes,
            )
    elif scene_id == 'friend_vignette':
        before = play.state
        play.act(
            'let_nia_take_the_search_list',
            requires={'friend.agency_vignette': False, 'friend.helping': False},
            **{'friend.agency_vignette': True, 'friend.helping': True, 'friend.trust': before['friend.trust'] + 1},
        )
    elif scene_id == 'shelf_vignette':
        play.act(
            'let_nia_explain_the_picture_spine_labels',
            requires={'friend.shelf_vignette': False, 'friend.shelf_skill': False},
            **{'friend.shelf_vignette': True, 'friend.shelf_skill': True},
        )
    elif scene_id == 'ending_found':
        if play.state['friend.bookmark_vignette']:
            play.act(
                'place_the_shared_bookmark_inside_the_recovered_book',
                requires={'bookmark.location': 'Lio', 'book.location': 'trolley'},
                **{'bookmark.location': 'book'},
            )
        play.act(
            'hand_nia_her_recovered_library_book',
            requires={'book.found': True, 'book.location': 'trolley', 'promise.status': 'made'},
            **{'book.location': 'Nia', 'promise.status': 'kept', 'friend.trust': play.state['friend.trust'] + 1},
        )
        play.act(
            'return_the_useful_trolley_to_its_bay',
            requires={'trolley.owner': 'Lio', 'trolley.useful': True},
            **{'trolley.owner': 'library', 'trolley.location': 'return_bay'},
        )
        play.act(
            'finish_the_kept_promise_before_closing',
            requires={'book.location': 'Nia', 'library.closed': False, 'trolley.location': 'return_bay'},
            **{'story.ended': True, 'story.outcome': 'promise_kept'},
        )
    else:
        play.act(
            'tell_nia_the_search_failed_and_choose_another_book',
            requires={'book.found': False, 'promise.status': 'made'},
            **{'promise.status': 'honest', 'friend.substitute_book': 'The Cloud Garden',
               'friend.trust': play.state['friend.trust'] + 1},
        )
        if play.state['friend.bookmark_vignette']:
            play.act(
                'return_the_shared_bookmark_to_nia',
                requires={'bookmark.location': 'Lio'},
                **{'bookmark.location': 'Nia'},
            )
        play.act(
            'return_the_useful_trolley_to_its_bay',
            requires={'trolley.owner': 'Lio', 'trolley.useful': True},
            **{'trolley.owner': 'library', 'trolley.location': 'return_bay'},
        )
        play.act(
            'finish_honestly_with_a_substitute_picture_book',
            requires={'promise.status': 'honest', 'friend.substitute_book': 'The Cloud Garden',
                      'trolley.location': 'return_bay'},
            **{'story.ended': True, 'story.outcome': 'promise_not_kept_honestly'},
        )
    after = deepcopy(play.state)
    validate(after)
    return {
        'id': scene_id, 'before': deepcopy(state), 'after': after,
        'events': deepcopy(play.events), 'text': render(scene_id, params, state, after),
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    state = initial(params)
    episodes = []
    used = set()
    for scene_id in path:
        if scene_id in used:
            raise StoryError('A scene cannot be repeated')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode['after']
        used.add(scene_id)
        if state['story.ended'] and scene_id != path[-1]:
            raise StoryError('No scene may follow an ending')
    return episodes


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise ValueError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    nodes = 0
    failed = set()

    def visit(state, episodes, used):
        nonlocal attempts, nodes
        nodes += 1
        if nodes > 20000:
            raise StoryError('Bounded scene search exhausted its node budget')
        remaining = count - len(episodes)
        if state['story.ended']:
            return episodes if remaining == 0 else None
        if remaining <= 0:
            return None
        signature = json.dumps([state, sorted(used), remaining], sort_keys=True, ensure_ascii=False)
        if signature in failed:
            return None
        choices = [sid for sid in SCENES if sid not in used and guard(sid, state)]
        if remaining == 1:
            choices = [sid for sid in choices if sid in ENDINGS]
        else:
            choices = [sid for sid in choices if sid not in ENDINGS]
        rng.shuffle(choices)
        for sid in choices:
            attempts += 1
            if attempts > 30000:
                raise StoryError('Bounded scene search exhausted its attempt budget')
            episode = play_scene(p, state, sid)
            result = visit(episode['after'], episodes + [episode], used | {sid})
            if result is not None:
                return result
        failed.add(signature)
        return None

    episodes = visit(initial(p), [], set())
    if episodes is None:
        raise StoryError('No compatible complete route at the requested length')
    story = '\n\n'.join(episode['text'] for episode in episodes)
    return {
        'seed': seed, 'parameters': asdict(p), 'scene_count': count,
        'path': [episode['id'] for episode in episodes], 'story': story,
        'episodes': episodes, 'final_state': deepcopy(episodes[-1]['after']),
        'search_attempts': attempts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', type=Path, help='JSON file containing Parameters fields')
    args = parser.parse_args()
    overrides = json.loads(args.params.read_text(encoding='utf-8')) if args.params else None
    p = Parameters(**overrides) if overrides is not None else None
    row = generate(args.seed, count=args.scenes, params=p)
    print(row['story'])


if __name__ == '__main__':
    main()
