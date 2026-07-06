import { AppComponent } from './app.component';

describe('AppComponent', () => {
  let component: AppComponent;

  beforeEach(() => {
    component = new AppComponent({} as never);
  });

  it('deduplicates and ignores malformed verb pairs', () => {
    const pairs = (component as never as { parsePairs(raw: string): Array<{ es: string; gl: string }> }).parsePairs(
      'amar\tamar\tV\namar\tamar\tV\ncomer\tcomer\tV\nmalformed\n'
    );

    expect(pairs).toEqual([
      { es: 'amar', gl: 'amar' },
      { es: 'comer', gl: 'comer' }
    ]);
  });

  it('links alignment rows to the latest infinitive pair marker', () => {
    const alignments = (component as never as { parseAlignments(raw: string): Array<{ es: string; gl: string; pairEs: string; pairGl: string }> }).parseAlignments(
      'amar\tamar\tFN-FN\tInf\namo\tamo\tPRS\tP1\ncomer\tcomer\tFN-FN\tInf\ncomo\tcomo\tPRS\tP1\n'
    );

    expect(alignments[1]).toEqual(jasmine.objectContaining({ es: 'amo', gl: 'amo', pairEs: 'amar', pairGl: 'amar' }));
    expect(alignments[3]).toEqual(jasmine.objectContaining({ es: 'como', gl: 'como', pairEs: 'comer', pairGl: 'comer' }));
  });

  it('filters alignments by pair, tense, person and normalized search terms', () => {
    component.alignments = [
      { es: 'amar', gl: 'amar', tense: 'FN-FN', person: 'Inf', pairEs: 'amar', pairGl: 'amar' },
      { es: 'amo', gl: 'amo', tense: 'PRS', person: 'P1', pairEs: 'amar', pairGl: 'amar' },
      { es: 'comía', gl: 'comía', tense: 'PST', person: 'P1', pairEs: 'comer', pairGl: 'comer' }
    ];
    component.selectedPair = { es: 'amar', gl: 'amar' };
    component.selectedTense = 'PRS';
    component.selectedPerson = 'P1';
    component.alignmentSearch = '  AMO  ';

    component.applyAlignmentFilters();

    expect(component.alignmentSearch).toBe('amo');
    expect(component.filteredAlignments).toEqual([
      { es: 'amo', gl: 'amo', tense: 'PRS', person: 'P1', pairEs: 'amar', pairGl: 'amar' }
    ]);
  });
});
