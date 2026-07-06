import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { catchError, forkJoin, of } from 'rxjs';

type PairSortField = 'es' | 'gl' | 'alignmentCount';
type AlignmentSortField = 'pairEs' | 'pairGl' | 'es' | 'gl' | 'tense' | 'person';
type SortDirection = 'asc' | 'desc';

interface VerbPair {
  key: string;
  es: string;
  gl: string;
  alignmentCount: number;
  searchBlob: string;
}

interface Alignment {
  es: string;
  gl: string;
  tense: string;
  person: string;
  pairEs: string;
  pairGl: string;
  pairKey: string;
  searchBlob: string;
}

interface PairAggregate {
  count: number;
  parts: string[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  pairSearch = '';
  alignmentSearch = '';
  selectedPair: VerbPair | null = null;
  selectedTense = 'ALL';
  selectedPerson = 'ALL';
  pairSortField: PairSortField = 'es';
  pairSortDirection: SortDirection = 'asc';
  alignmentSortField: AlignmentSortField = 'pairEs';
  alignmentSortDirection: SortDirection = 'asc';

  loadingPairs = true;
  loadingAlignments = true;

  pairs: VerbPair[] = [];
  filteredPairs: VerbPair[] = [];

  alignments: Alignment[] = [];
  filteredAlignments: Alignment[] = [];

  tenseOptions: string[] = [];
  personOptions: string[] = [];

  errorMessage = '';

  readonly maxRows = 300;
  readonly maxQueryLength = 120;

  constructor(private readonly http: HttpClient) {}

  ngOnInit(): void {
    this.loadData();
  }

  private loadData(): void {
    forkJoin({
      pairsRaw: this.http.get('assets/data/verbos_relacionados.tsv', { responseType: 'text' }),
      alignmentsRaw: this.http
        .get('assets/data/alineaciones_completas.tsv', { responseType: 'text' })
        .pipe(catchError(() => of('')))
    }).subscribe({
      next: ({ pairsRaw, alignmentsRaw }) => {
        const pairAggregates = new Map<string, PairAggregate>();

        this.alignments = alignmentsRaw ? this.parseAlignments(alignmentsRaw, pairAggregates) : [];
        this.pairs = this.parsePairs(pairsRaw, pairAggregates);
        this.tenseOptions = this.buildOptions(this.alignments.map((x) => x.tense));
        this.personOptions = this.buildOptions(this.alignments.map((x) => x.person));

        this.loadingPairs = false;
        this.loadingAlignments = false;
        this.errorMessage = '';

        this.applyPairFilters();
        this.applyAlignmentFilters();
      },
      error: () => {
        this.loadingPairs = false;
        this.loadingAlignments = false;
        this.errorMessage =
          'No se pudo cargar el listado de pares. Comprueba assets/data/verbos_relacionados.tsv';
      }
    });
  }

  private parsePairs(raw: string, pairAggregates: Map<string, PairAggregate>): VerbPair[] {
    const seen = new Set<string>();
    const out: VerbPair[] = [];

    for (const line of raw.split(/\r?\n/)) {
      if (!line.trim()) {
        continue;
      }

      const [es, gl] = line.split('\t');
      if (!es || !gl) {
        continue;
      }

      const cleanEs = es.trim();
      const cleanGl = gl.trim();
      const key = this.buildPairKey(cleanEs, cleanGl);
      if (seen.has(key)) {
        continue;
      }

      seen.add(key);
      const aggregate = pairAggregates.get(key);
      out.push({
        key,
        es: cleanEs,
        gl: cleanGl,
        alignmentCount: aggregate?.count ?? 0,
        searchBlob: this.normalizeText(
          `${cleanEs} ${cleanGl} ${aggregate?.parts.join(' ') ?? ''}`
        )
      });
    }

    return out;
  }

  private parseAlignments(raw: string, pairAggregates: Map<string, PairAggregate>): Alignment[] {
    const out: Alignment[] = [];
    let currentPairEs = '';
    let currentPairGl = '';

    for (const line of raw.split(/\r?\n/)) {
      if (!line.trim()) {
        continue;
      }

      const parts = line.split('\t');
      if (parts.length < 4) {
        continue;
      }

      const formEs = parts[0].trim();
      const formGl = parts[1].trim();
      const tense = parts[2].trim();
      const person = parts[3].trim();

      if (tense === 'FN-FN' && person === 'Inf') {
        currentPairEs = formEs;
        currentPairGl = formGl;
      }

      if (!currentPairEs || !currentPairGl) {
        continue;
      }

      const pairKey = this.buildPairKey(currentPairEs, currentPairGl);
      const searchBlob = this.normalizeText(
        `${formEs} ${formGl} ${tense} ${person} ${currentPairEs} ${currentPairGl}`
      );

      out.push({
        es: formEs,
        gl: formGl,
        tense,
        person,
        pairEs: currentPairEs,
        pairGl: currentPairGl,
        pairKey,
        searchBlob
      });

      const aggregate = pairAggregates.get(pairKey) ?? { count: 0, parts: [] };
      aggregate.count += 1;
      aggregate.parts.push(formEs, formGl, tense, person);
      pairAggregates.set(pairKey, aggregate);
    }

    return out;
  }

  private buildOptions(values: string[]): string[] {
    return [...new Set(values)].sort((a, b) => this.compareText(a, b));
  }

  private buildPairKey(es: string, gl: string): string {
    return `${this.normalizeText(es)}|${this.normalizeText(gl)}`;
  }

  private normalizeText(raw: string): string {
    return raw
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[\u0000-\u001F\u007F]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  private normalizeQuery(raw: string): string {
    return this.normalizeText(raw).slice(0, this.maxQueryLength);
  }

  private compareText(a: string, b: string): number {
    return a.localeCompare(b, 'es', { sensitivity: 'base' });
  }

  private directionFactor(direction: SortDirection): number {
    return direction === 'asc' ? 1 : -1;
  }

  onPairSearchChange(): void {
    this.applyPairFilters();
  }

  onPairSortFieldChange(): void {
    this.applyPairFilters();
  }

  togglePairSortDirection(): void {
    this.pairSortDirection = this.pairSortDirection === 'asc' ? 'desc' : 'asc';
    this.applyPairFilters();
  }

  choosePair(pair: VerbPair): void {
    this.selectedPair = pair;
    this.applyAlignmentFilters();
  }

  clearPair(): void {
    this.selectedPair = null;
    this.applyAlignmentFilters();
  }

  clearAlignmentFilters(): void {
    this.selectedTense = 'ALL';
    this.selectedPerson = 'ALL';
    this.alignmentSearch = '';
    this.applyAlignmentFilters();
  }

  setAlignmentSort(field: AlignmentSortField): void {
    if (this.alignmentSortField === field) {
      this.alignmentSortDirection = this.alignmentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.alignmentSortField = field;
      this.alignmentSortDirection = 'asc';
    }

    this.applyAlignmentFilters();
  }

  private applyPairFilters(): void {
    const terms = this.normalizeQuery(this.pairSearch).split(/\s+/).filter(Boolean);

    this.filteredPairs = this.pairs
      .filter((pair) => terms.every((term) => pair.searchBlob.includes(term)))
      .sort((a, b) => this.comparePairs(a, b));
  }

  applyAlignmentFilters(): void {
    const terms = this.normalizeQuery(this.alignmentSearch).split(/\s+/).filter(Boolean);

    this.filteredAlignments = this.alignments
      .filter((row) => {
        if (this.selectedTense !== 'ALL' && row.tense !== this.selectedTense) {
          return false;
        }

        if (this.selectedPerson !== 'ALL' && row.person !== this.selectedPerson) {
          return false;
        }

        if (this.selectedPair && row.pairKey !== this.selectedPair.key) {
          return false;
        }

        return terms.every((term) => row.searchBlob.includes(term));
      })
      .sort((a, b) => this.compareAlignments(a, b));
  }

  private comparePairs(a: VerbPair, b: VerbPair): number {
    const factor = this.directionFactor(this.pairSortDirection);

    if (this.pairSortField === 'alignmentCount') {
      const countDiff = (a.alignmentCount - b.alignmentCount) * factor;
      if (countDiff !== 0) {
        return countDiff;
      }
    } else {
      const fieldDiff = this.compareText(a[this.pairSortField], b[this.pairSortField]) * factor;
      if (fieldDiff !== 0) {
        return fieldDiff;
      }
    }

    return this.compareText(a.es, b.es) || this.compareText(a.gl, b.gl);
  }

  private compareAlignments(a: Alignment, b: Alignment): number {
    const factor = this.directionFactor(this.alignmentSortDirection);
    const primaryDiff =
      this.compareText(a[this.alignmentSortField], b[this.alignmentSortField]) * factor;

    if (primaryDiff !== 0) {
      return primaryDiff;
    }

    return (
      this.compareText(a.pairEs, b.pairEs) ||
      this.compareText(a.pairGl, b.pairGl) ||
      this.compareText(a.tense, b.tense) ||
      this.compareText(a.person, b.person) ||
      this.compareText(a.es, b.es) ||
      this.compareText(a.gl, b.gl)
    );
  }

  trackPair(_index: number, pair: VerbPair): string {
    return pair.key;
  }

  trackAlignment(_index: number, row: Alignment): string {
    return `${row.pairKey}|${row.es}|${row.gl}|${row.tense}|${row.person}`;
  }

  get visibleAlignments(): Alignment[] {
    return this.filteredAlignments.slice(0, this.maxRows);
  }

  get hiddenAlignmentCount(): number {
    return Math.max(this.filteredAlignments.length - this.visibleAlignments.length, 0);
  }

  get pairSearchSummary(): string {
    return this.pairSearch.trim()
      ? `${this.filteredPairs.length.toLocaleString('es-ES')} pares coinciden`
      : `${this.pairs.length.toLocaleString('es-ES')} pares disponibles`;
  }

  get alignmentSortLabel(): string {
    return this.alignmentSortDirection === 'asc' ? 'ascendente' : 'descendente';
  }

  getPairSortLabel(): string {
    return this.pairSortDirection === 'asc' ? 'A-Z' : 'Z-A';
  }

  getAlignmentHeaderLabel(field: AlignmentSortField): string {
    if (this.alignmentSortField !== field) {
      return '';
    }

    return this.alignmentSortDirection === 'asc' ? '▲' : '▼';
  }
}
