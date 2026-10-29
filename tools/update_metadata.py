"""Update provenance from local evidence without manufacturing scientific acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup
from build_book import original_body, read

ROOT = Path(__file__).resolve().parents[1]


def load(path, default):
    return json.loads(read(path)) if path.is_file() else default


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')


def main():
    manifest = load(ROOT / 'source-manifest.json', {})
    integrity = load(ROOT / 'work/audio-integrity.json', None)
    if integrity is None:
        raise SystemExit('Private acquisition evidence is absent. Rebuild the reader '
                         'with build_book.py; published sidecars remain reusable.')
    by_id = {row['id']: row for row in integrity}
    reading = load(ROOT / 'work/reading-ledger.json', {})
    transcripts = {}
    for recording in manifest['lectures']:
        identity = recording['id']
        transcripts[identity] = load(ROOT / 'work/sources' / (identity + '.asr.json'), {})
    inventory = []
    for chapter in manifest['chapters']:
        number = int(chapter['order'])
        paths = sorted(ROOT.glob(f'chapter-{number:02d}-*.html'))
        if not paths:
            continue
        if len(paths) != 1:
            raise ValueError('Ambiguous chapter identity')
        path = paths[0]
        body = original_body(read(path))
        checksum = hashlib.sha256(body.encode('utf-8')).hexdigest()
        soup = BeautifulSoup(body, 'html.parser')
        prior = load(path.with_suffix('.meta.json'), {})
        reviews = prior.get('independent_review', {})
        accepted = (reviews.get('accepted', False)
                    and reviews.get('accepted_body_sha256') == checksum)
        if not accepted and reviews.get('accepted'):
            reviews = {'accepted': False, 'reason': 'Body digest changed; re-review required',
                       'previous_acceptance': reviews}
        assigned = [row for row in manifest['lectures'] if row['chapter_order'] == number]
        source_rows = []
        for recording in assigned:
            identity = recording['id']
            audio = by_id.get(identity, {})
            transcript = transcripts[identity]
            segments = transcript.get('segments', [])
            source_rows.append({
                'video_id': identity,
                'playlist_position': recording['playlist_position'],
                'lecture_label': recording['label'],
                'duration_seconds': recording['duration'],
                'decoded_audio_duration_seconds': audio.get('decoded_audio_duration'),
                'complete_decoded_audio': audio.get('complete_decoded_audio', False),
                'media_sha256': audio.get('audio_sha256'),
                'machine_transcript_complete': transcript.get('complete', False),
                'sequential_transcript_reading_complete': reading.get(identity, {}).get(
                    'complete_sequential_reading', False),
                'transcript_first_start': segments[0]['start'] if segments else None,
                'transcript_last_end': segments[-1]['end'] if segments else None,
                'transcript_provenance': transcript.get('source_type', 'No complete transcript'),
                'asr_method': {key: transcript.get(key) for key in (
                    'model', 'beam_size', 'chunk_core_seconds', 'chunk_overlap_seconds',
                    'chunk_boundary_method', 'source_asr_video_id', 'reused_asr_of', 'duplicate_basis') if key in transcript},
            })
        sections = []
        for heading in soup.select('h2'):
            sections.append({
                'section': heading.get_text(' ', strip=True),
                'anchor': heading.get('id'), 'video_id': heading.get('data-video'),
                'start': int(heading['data-start']) if heading.has_attr('data-start') else None,
                'end': int(heading['data-end']) if heading.has_attr('data-end') else None,
                'lecture_material': 'Related topic located by the stated recording span'
                                    if heading.has_attr('data-video') else '',
                'research_extension': 'Specific inspected primary support is cited locally',
                'teaching_construction': 'Original exposition, proofs, examples, code and '
                                         'solutions; a timestamp does not attribute every '
                                         'statement to the recording',
            })
        old_refs = {row['url']: row for row in prior.get('references', [])}
        references = {}
        for anchor in soup.select('a[href]'):
            url = anchor['href']
            if url.startswith('https://') and 'youtube.com' not in url:
                canonical = url.split('#', 1)[0]
                references[canonical] = old_refs.get(canonical, {
                    'url': canonical, 'title': anchor.get_text(' ', strip=True),
                    'supports': 'Exact claim and locator are stated beside the chapter citation',
                })
        meta = {'chapter': number, 'title': chapter['title'],
                'status': 'reviewed — two independent AI scientific reviews' if accepted
                          else 'authored; independent scientific acceptance pending',
                'authored_body_sha256': checksum, 'recordings': source_rows,
                'sections': sections, 'references': list(references.values()),
                'prose_words_including_math': len(soup.get_text(' ', strip=True).split()),
                'solution_count': len(soup.select('details')),
                'executable_listing_count': len(soup.select('pre[data-run]')),
                'independent_review': reviews,
                'visual_boundary': 'No comprehensive audiovisual or board transcription; '
                                   'machine recognition and chunk boundaries remain fallible.'}
        dump(path.with_suffix('.meta.json'), meta)
        chapter['chapter_status'] = meta['status']
        inventory.append({'chapter': number, 'file': path.name, 'body_sha256': checksum,
                          'words': meta['prose_words_including_math'],
                          'solutions': meta['solution_count'],
                          'listings': meta['executable_listing_count'],
                          'scientifically_accepted': bool(accepted)})
    accepted_by_chapter = {row['chapter']: row['scientifically_accepted'] for row in inventory}
    for recording in manifest['lectures']:
        identity = recording['id']
        has_audio = by_id.get(identity, {}).get('complete_decoded_audio', False)
        has_asr = bool(transcripts[identity].get('complete'))
        has_read = bool(reading.get(identity, {}).get('complete_sequential_reading'))
        if has_audio and has_asr and has_read:
            recording['source_status'] = ('Complete decoded audio and full machine transcript read; ' +
                ('exact chapter body accepted after two independent scientific reviews'
                 if accepted_by_chapter.get(recording['chapter_order']) else 'chapter scientific acceptance pending'))
        elif has_audio and has_asr:
            recording['source_status'] = 'Complete decoded audio and local machine transcript; sequential reading pending'
        elif has_audio:
            recording['source_status'] = 'Complete decoded audio verified; machine transcript and reading pending'
        else:
            recording['source_status'] = 'Complete source acquisition pending'
    editorial = []
    for row in inventory:
        meta = load(ROOT / row['file'].replace('.html', '.meta.json'), {})
        editorial.append({'chapter': row['chapter'], 'authored_body_sha256': row['body_sha256'],
                          'accepted': row['scientifically_accepted'],
                          'reviews': meta.get('independent_review', {}).get('rounds', [])})
    dump(ROOT / 'editorial-review-summary.json', {
        'scope': 'Recorded independent AI scientific reviews; acceptance binds only to an exact chapter body, not full-course completion.',
        'chapters': editorial})
    dump(ROOT / 'source-manifest.json', manifest)
    dump(ROOT / 'content-inventory.json', {
        'planned_chapter_count': len(manifest['chapters']),
        'authored_chapter_count': len(inventory), 'chapters': inventory,
        'prose_words_including_math': sum(row['words'] for row in inventory),
        'worked_solution_count': sum(row['solutions'] for row in inventory),
        'executable_listing_count': sum(row['listings'] for row in inventory),
        'counting_note': 'Whitespace tokens include math and code; inventory is not a pure '
                         'prose estimate or a scientific completion verdict.'})
    dump(ROOT / 'source-validation-summary.json', {
        'recording_count': len(manifest['lectures']),
        'unique_acquired_audio_representations': len({row['audio_sha256'] for row in integrity}),
        'complete_decoded_audio_count': sum(row.get('complete_decoded_audio', False)
                                            for row in integrity),
        'complete_machine_transcript_count': sum(bool(row.get('complete'))
                                                  for row in transcripts.values()),
        'complete_sequential_transcript_reading_count': sum(
            bool(reading.get(row['id'], {}).get('complete_sequential_reading'))
            for row in manifest['lectures']),
        'caption_acquisition': 'Publisher transcript URLs absent; YouTube caption HTTP429; '
                               'official VTT candidate403. Local small.en ASR used.',
        'duration_method': 'Decoded sample count at16000Hz, not container duration estimates.',
        'largest_absolute_duration_difference_seconds': max(
            (row['duration_difference'] for row in integrity), default=None),
        'recordings': integrity,
        'scope_limit': 'Audio acquisition, ASR, sequential reading and scientific acceptance '
                       'are separate gates. No full audiovisual/board audit is implied.'})
    print(len(inventory), 'chapter provenance sidecars updated; acceptance preserved only '
          'for unchanged reviewed digests')


if __name__ == '__main__':
    main()
