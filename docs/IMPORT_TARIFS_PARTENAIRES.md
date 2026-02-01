# Solutions d'Import des Tarifs Partenaires
## Import depuis fichiers PDF, Excel et CSV

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture d'import](#2-architecture-dimport)
3. [Import CSV](#3-import-csv)
4. [Import Excel](#4-import-excel)
5. [Import PDF](#5-import-pdf)
6. [Validation et transformation](#6-validation-et-transformation)
7. [Gestion des erreurs](#7-gestion-des-erreurs)
8. [Interface utilisateur](#8-interface-utilisateur)
9. [Comparatif des solutions PDF](#9-comparatif-des-solutions-pdf)

---

## 1. Vue d'ensemble

### 1.1 Flux d'import global

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUX D'IMPORT DES TARIFS                            │
│                                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                                      │
│  │   CSV   │  │  Excel  │  │   PDF   │                                      │
│  └────┬────┘  └────┬────┘  └────┬────┘                                      │
│       │            │            │                                           │
│       ▼            ▼            ▼                                           │
│  ┌──────────────────────────────────────────────────────────────-───────┐   │
│  │                         FILE UPLOAD                                  │   │
│  │                    (Validation format + taille)                      │   │
│  └─────────────────────────────────┬─────────────────────────────-──────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         PARSER ENGINE                               │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────────────────┐    │    │
│  │  │ CSV Parser│  │Excel Parse│  │        PDF Parser             │    │    │
│  │  │ (papaparse│  │ (exceljs) │  │  ┌───────-──┐  ┌───────────┐  │    │    │
│  │  └───────────┘  └───────────┘  │  │ pdf-parse│  │ OCR/IA    │  │    │    │
│  │                                │  │ (texte)  │  │ (images)  │  │    │    │
│  │                                │  └───-──────┘  └───────────┘  │    │    │
│  │                                └───────────────────────────────┘    │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       DATA TRANSFORMER                              │    │
│  │              (Mapping colonnes → schéma standard)                   │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         VALIDATOR                                   │    │
│  │              (Règles métier + cohérence données)                    │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│              ┌──────────┐                   ┌──────────┐                    │
│              │ Valides  │                   │ Erreurs  │                    │
│              └────┬─────┘                   └────┬─────┘                    │
│                   │                              │                          │
│                   ▼                              ▼                          │
│              ┌──────────┐                   ┌──────────┐                    │
│              │   INSERT │                   │  RAPPORT │                    │
│              │    BD    │                   │ D'ERREURS│                    │
│              └──────────┘                   └──────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Complexité par format

| Format | Complexité | Fiabilité | Automatisation |
|--------|------------|-----------|----------------|
| **CSV** | Faible | Haute | 100% |
| **Excel** | Moyenne | Haute | 100% |
| **PDF (texte)** | Moyenne | Moyenne | 80-90% |
| **PDF (scanné/image)** | Élevée | Variable | 60-80% |

---

## 2. Architecture d'import

### 2.1 Structure des modules

```
src/modules/partners/
├── import/
│   ├── import.module.ts
│   ├── import.controller.ts
│   ├── import.service.ts
│   │
│   ├── parsers/
│   │   ├── parser.interface.ts
│   │   ├── csv.parser.ts
│   │   ├── excel.parser.ts
│   │   ├── pdf.parser.ts
│   │   └── parser.factory.ts
│   │
│   ├── transformers/
│   │   ├── transformer.interface.ts
│   │   ├── column-mapper.ts
│   │   └── data-normalizer.ts
│   │
│   ├── validators/
│   │   ├── row-validator.ts
│   │   └── business-rules.validator.ts
│   │
│   ├── processors/
│   │   ├── batch.processor.ts
│   │   └── async-import.processor.ts
│   │
│   └── dto/
│       ├── import-file.dto.ts
│       ├── import-result.dto.ts
│       └── column-mapping.dto.ts
```

### 2.2 Interface commune des parsers

```typescript
// src/modules/partners/import/parsers/parser.interface.ts

export interface ParsedRow {
  rowNumber: number;
  data: Record<string, any>;
  raw: string | object;
}

export interface ParseResult {
  success: boolean;
  rows: ParsedRow[];
  headers: string[];
  errors: ParseError[];
  metadata: {
    totalRows: number;
    parsedRows: number;
    fileType: string;
    encoding?: string;
  };
}

export interface ParseError {
  row?: number;
  column?: string;
  message: string;
  type: 'format' | 'encoding' | 'structure' | 'extraction';
}

export interface FileParser {
  readonly supportedMimeTypes: string[];
  readonly supportedExtensions: string[];

  canParse(file: Express.Multer.File): boolean;
  parse(file: Express.Multer.File, options?: ParseOptions): Promise<ParseResult>;
}

export interface ParseOptions {
  encoding?: string;
  delimiter?: string;
  headerRow?: number;
  dataStartRow?: number;
  sheetName?: string;      // Pour Excel
  tableDetection?: boolean; // Pour PDF
  ocrEnabled?: boolean;     // Pour PDF scannés
}
```

### 2.3 Factory des parsers

```typescript
// src/modules/partners/import/parsers/parser.factory.ts

import { Injectable } from '@nestjs/common';
import { CsvParser } from './csv.parser';
import { ExcelParser } from './excel.parser';
import { PdfParser } from './pdf.parser';
import { FileParser } from './parser.interface';

@Injectable()
export class ParserFactory {
  private parsers: FileParser[];

  constructor(
    private csvParser: CsvParser,
    private excelParser: ExcelParser,
    private pdfParser: PdfParser,
  ) {
    this.parsers = [csvParser, excelParser, pdfParser];
  }

  getParser(file: Express.Multer.File): FileParser {
    const parser = this.parsers.find(p => p.canParse(file));

    if (!parser) {
      throw new UnsupportedFileTypeError(
        `Type de fichier non supporté: ${file.mimetype}`
      );
    }

    return parser;
  }

  getSupportedTypes(): string[] {
    return this.parsers.flatMap(p => p.supportedExtensions);
  }
}
```

---

## 3. Import CSV

### 3.1 Librairie recommandée

**PapaParse** - La plus performante et robuste pour Node.js

```bash
npm install papaparse @types/papaparse
```

### 3.2 Implémentation

```typescript
// src/modules/partners/import/parsers/csv.parser.ts

import { Injectable } from '@nestjs/common';
import * as Papa from 'papaparse';
import * as iconv from 'iconv-lite';
import { FileParser, ParseResult, ParseOptions, ParsedRow } from './parser.interface';

@Injectable()
export class CsvParser implements FileParser {
  readonly supportedMimeTypes = ['text/csv', 'text/plain', 'application/csv'];
  readonly supportedExtensions = ['.csv', '.txt'];

  canParse(file: Express.Multer.File): boolean {
    const ext = this.getExtension(file.originalname);
    return (
      this.supportedMimeTypes.includes(file.mimetype) ||
      this.supportedExtensions.includes(ext)
    );
  }

  async parse(file: Express.Multer.File, options?: ParseOptions): Promise<ParseResult> {
    const encoding = options?.encoding || this.detectEncoding(file.buffer);
    const content = iconv.decode(file.buffer, encoding);

    return new Promise((resolve) => {
      Papa.parse(content, {
        header: true,
        skipEmptyLines: true,
        delimiter: options?.delimiter || '',  // Auto-detect
        dynamicTyping: true,
        transformHeader: (header) => this.normalizeHeader(header),

        complete: (results) => {
          const rows: ParsedRow[] = results.data.map((row, index) => ({
            rowNumber: index + 2, // +2 car header = ligne 1
            data: row as Record<string, any>,
            raw: row,
          }));

          const errors = results.errors.map(err => ({
            row: err.row,
            message: err.message,
            type: 'format' as const,
          }));

          resolve({
            success: errors.length === 0,
            rows,
            headers: results.meta.fields || [],
            errors,
            metadata: {
              totalRows: results.data.length,
              parsedRows: rows.length,
              fileType: 'csv',
              encoding,
            },
          });
        },
      });
    });
  }

  private detectEncoding(buffer: Buffer): string {
    // Détection BOM UTF-8
    if (buffer[0] === 0xEF && buffer[1] === 0xBB && buffer[2] === 0xBF) {
      return 'utf-8';
    }
    // Détection BOM UTF-16 LE
    if (buffer[0] === 0xFF && buffer[1] === 0xFE) {
      return 'utf-16le';
    }
    // Par défaut UTF-8, sinon tenter ISO-8859-1 pour les accents
    return 'utf-8';
  }

  private normalizeHeader(header: string): string {
    return header
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '');
  }

  private getExtension(filename: string): string {
    return filename.slice(filename.lastIndexOf('.')).toLowerCase();
  }
}
```

### 3.3 Format CSV attendu

```csv
mode_transport,origine_cp,origine_ville,origine_pays,destination_cp,destination_ville,destination_pays,poids_min,poids_max,volume_min,volume_max,prix,devise,delai,validite
road,75000,Paris,FR,1000,Brussels,BE,0,1000,0,10,120.50,EUR,48h,2025-12-31
rail,75000,Paris,FR,20121,Milan,IT,0,5000,0,50,350.00,EUR,72h,2025-12-31
sea,13000,Marseille,FR,310,Shanghai,CN,0,20000,0,100,2500.00,EUR,30d,2025-12-31
```

---

## 4. Import Excel

### 4.1 Librairie recommandée

**ExcelJS** - Complète et performante

```bash
npm install exceljs
```

### 4.2 Implémentation

```typescript
// src/modules/partners/import/parsers/excel.parser.ts

import { Injectable } from '@nestjs/common';
import * as ExcelJS from 'exceljs';
import { FileParser, ParseResult, ParseOptions, ParsedRow, ParseError } from './parser.interface';

@Injectable()
export class ExcelParser implements FileParser {
  readonly supportedMimeTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
  ];
  readonly supportedExtensions = ['.xlsx', '.xls'];

  canParse(file: Express.Multer.File): boolean {
    const ext = file.originalname.slice(file.originalname.lastIndexOf('.')).toLowerCase();
    return (
      this.supportedMimeTypes.includes(file.mimetype) ||
      this.supportedExtensions.includes(ext)
    );
  }

  async parse(file: Express.Multer.File, options?: ParseOptions): Promise<ParseResult> {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(file.buffer);

    // Sélectionner la feuille
    const worksheet = options?.sheetName
      ? workbook.getWorksheet(options.sheetName)
      : workbook.worksheets[0];

    if (!worksheet) {
      return {
        success: false,
        rows: [],
        headers: [],
        errors: [{ message: 'Aucune feuille trouvée', type: 'structure' }],
        metadata: { totalRows: 0, parsedRows: 0, fileType: 'excel' },
      };
    }

    const headerRowNum = options?.headerRow || 1;
    const dataStartRow = options?.dataStartRow || 2;

    // Extraire les headers
    const headerRow = worksheet.getRow(headerRowNum);
    const headers: string[] = [];
    headerRow.eachCell((cell, colNumber) => {
      headers[colNumber - 1] = this.normalizeHeader(cell.text);
    });

    // Extraire les données
    const rows: ParsedRow[] = [];
    const errors: ParseError[] = [];

    worksheet.eachRow((row, rowNumber) => {
      if (rowNumber < dataStartRow) return;

      const rowData: Record<string, any> = {};
      let hasData = false;

      row.eachCell((cell, colNumber) => {
        const header = headers[colNumber - 1];
        if (header) {
          rowData[header] = this.extractCellValue(cell);
          if (rowData[header] !== null && rowData[header] !== '') {
            hasData = true;
          }
        }
      });

      // Ignorer les lignes vides
      if (hasData) {
        rows.push({
          rowNumber,
          data: rowData,
          raw: row.values,
        });
      }
    });

    return {
      success: errors.length === 0,
      rows,
      headers: headers.filter(h => h),
      errors,
      metadata: {
        totalRows: worksheet.rowCount - headerRowNum,
        parsedRows: rows.length,
        fileType: 'excel',
      },
    };
  }

  private extractCellValue(cell: ExcelJS.Cell): any {
    if (cell.type === ExcelJS.ValueType.Date) {
      return cell.value;
    }
    if (cell.type === ExcelJS.ValueType.Number) {
      return cell.value;
    }
    if (cell.type === ExcelJS.ValueType.Formula) {
      return cell.result;
    }
    if (cell.type === ExcelJS.ValueType.RichText) {
      return (cell.value as ExcelJS.CellRichTextValue).richText
        .map(rt => rt.text)
        .join('');
    }
    return cell.text?.trim() || null;
  }

  private normalizeHeader(header: string): string {
    return header
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_àâäéèêëïîôùûüç]/g, '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }
}
```

### 4.3 Template Excel recommandé

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ A              │ B          │ C           │ D      │ E              │ ...       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Mode Transport │ Origine CP │ Origine Ville│Origine │ Destination CP │ ...       │
│                │            │              │ Pays   │                │           │
├─────────────────────────────────────────────────────────────────────────────────┤
│ road           │ 75000      │ Paris        │ FR     │ 1000           │ ...       │
│ rail           │ 75000      │ Paris        │ FR     │ 20121          │ ...       │
│ sea            │ 13000      │ Marseille    │ FR     │ 310            │ ...       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Import PDF

### 5.1 Complexité des PDF

Les PDF peuvent contenir :

| Type de contenu | Complexité | Solution |
|-----------------|------------|----------|
| Texte natif | Faible | pdf-parse, pdf.js |
| Tableaux structurés | Moyenne | Tabula, Camelot |
| Images/Scans | Élevée | OCR (Tesseract) |
| Formulaires complexes | Élevée | IA (GPT-4 Vision, Claude) |

### 5.2 Solution 1 : PDF avec texte natif (pdf-parse)

```bash
npm install pdf-parse
```

```typescript
// src/modules/partners/import/parsers/pdf-text.parser.ts

import { Injectable } from '@nestjs/common';
import * as pdfParse from 'pdf-parse';

@Injectable()
export class PdfTextParser {
  async extractText(buffer: Buffer): Promise<string> {
    const data = await pdfParse(buffer);
    return data.text;
  }

  async extractTables(buffer: Buffer): Promise<string[][]> {
    const text = await this.extractText(buffer);
    return this.parseTextToTable(text);
  }

  private parseTextToTable(text: string): string[][] {
    const lines = text.split('\n').filter(line => line.trim());
    const rows: string[][] = [];

    for (const line of lines) {
      // Détection des séparateurs (espaces multiples, tabulations)
      const cells = line
        .split(/\s{2,}|\t/)
        .map(cell => cell.trim())
        .filter(cell => cell);

      if (cells.length > 1) {
        rows.push(cells);
      }
    }

    return rows;
  }
}
```

### 5.3 Solution 2 : PDF avec tableaux (Tabula via Python)

**Tabula** est l'outil le plus fiable pour extraire des tableaux PDF.

```bash
# Installation
pip install tabula-py
```

```typescript
// src/modules/partners/import/parsers/pdf-tabula.parser.ts

import { Injectable } from '@nestjs/common';
import { spawn } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

@Injectable()
export class PdfTabulaParser {
  async extractTables(buffer: Buffer): Promise<any[]> {
    // Sauvegarder temporairement le fichier
    const tempFile = path.join(os.tmpdir(), `import_${Date.now()}.pdf`);
    const outputFile = path.join(os.tmpdir(), `import_${Date.now()}.json`);

    try {
      await fs.writeFile(tempFile, buffer);

      // Appeler le script Python
      await this.runTabula(tempFile, outputFile);

      // Lire le résultat
      const result = await fs.readFile(outputFile, 'utf-8');
      return JSON.parse(result);
    } finally {
      // Nettoyer
      await fs.unlink(tempFile).catch(() => {});
      await fs.unlink(outputFile).catch(() => {});
    }
  }

  private runTabula(inputFile: string, outputFile: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const process = spawn('python3', [
        '-c',
        `
import tabula
import json

tables = tabula.read_pdf('${inputFile}', pages='all', multiple_tables=True)
result = [table.to_dict('records') for table in tables]

with open('${outputFile}', 'w') as f:
    json.dump(result, f)
        `,
      ]);

      process.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Tabula exited with code ${code}`));
      });

      process.on('error', reject);
    });
  }
}
```

### 5.4 Solution 3 : PDF scannés avec OCR (Tesseract)

```bash
# Installation système
brew install tesseract tesseract-lang  # macOS
apt-get install tesseract-ocr tesseract-ocr-fra  # Ubuntu

# Installation Node.js
npm install tesseract.js sharp
```

```typescript
// src/modules/partners/import/parsers/pdf-ocr.parser.ts

import { Injectable, Logger } from '@nestjs/common';
import Tesseract from 'tesseract.js';
import * as sharp from 'sharp';
import { fromBuffer } from 'pdf2pic';

@Injectable()
export class PdfOcrParser {
  private readonly logger = new Logger(PdfOcrParser.name);

  async extractTextFromScannedPdf(buffer: Buffer): Promise<string[]> {
    // Convertir PDF en images
    const images = await this.pdfToImages(buffer);

    // OCR sur chaque page
    const texts: string[] = [];
    for (const imageBuffer of images) {
      const text = await this.ocrImage(imageBuffer);
      texts.push(text);
    }

    return texts;
  }

  private async pdfToImages(buffer: Buffer): Promise<Buffer[]> {
    const converter = fromBuffer(buffer, {
      density: 300,
      format: 'png',
      width: 2480,
      height: 3508,
    });

    const images: Buffer[] = [];
    let page = 1;

    while (true) {
      try {
        const result = await converter(page);
        if (result.buffer) {
          images.push(result.buffer);
        }
        page++;
      } catch {
        break; // Plus de pages
      }
    }

    return images;
  }

  private async ocrImage(imageBuffer: Buffer): Promise<string> {
    // Prétraitement de l'image pour améliorer l'OCR
    const processedImage = await sharp(imageBuffer)
      .greyscale()
      .normalize()
      .sharpen()
      .toBuffer();

    const { data: { text } } = await Tesseract.recognize(
      processedImage,
      'fra+eng', // Français + Anglais
      {
        logger: (m) => this.logger.debug(m),
      }
    );

    return text;
  }
}
```

### 5.5 Solution 4 : PDF complexes avec IA (Claude/GPT-4)

Pour les PDF avec des formats très variables ou complexes, utiliser une IA multimodale.

```typescript
// src/modules/partners/import/parsers/pdf-ai.parser.ts

import { Injectable } from '@nestjs/common';
import Anthropic from '@anthropic-ai/sdk';
import * as sharp from 'sharp';
import { fromBuffer } from 'pdf2pic';

interface ExtractedQuote {
  transport_mode: string;
  origin: { city: string; country: string; postal_code?: string };
  destination: { city: string; country: string; postal_code?: string };
  weight_range?: { min: number; max: number };
  volume_range?: { min: number; max: number };
  cost: number;
  currency: string;
  delivery_time?: string;
}

@Injectable()
export class PdfAiParser {
  private anthropic: Anthropic;

  constructor() {
    this.anthropic = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });
  }

  async extractQuotesFromPdf(buffer: Buffer): Promise<ExtractedQuote[]> {
    // Convertir PDF en images
    const images = await this.pdfToImages(buffer);

    const allQuotes: ExtractedQuote[] = [];

    for (const imageBuffer of images) {
      const quotes = await this.extractFromImage(imageBuffer);
      allQuotes.push(...quotes);
    }

    return allQuotes;
  }

  private async extractFromImage(imageBuffer: Buffer): Promise<ExtractedQuote[]> {
    const base64Image = imageBuffer.toString('base64');

    const response = await this.anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'image',
              source: {
                type: 'base64',
                media_type: 'image/png',
                data: base64Image,
              },
            },
            {
              type: 'text',
              text: `Analyse cette image d'un document de tarifs de transport.

Extrais TOUS les tarifs de transport présents sous forme de JSON.

Pour chaque tarif, extrais:
- transport_mode: "road", "rail", "sea", "air" ou "multimodal"
- origin: { city, country (code ISO 2 lettres), postal_code (si disponible) }
- destination: { city, country (code ISO 2 lettres), postal_code (si disponible) }
- weight_range: { min, max } en kg (si applicable)
- volume_range: { min, max } en m³ (si applicable)
- cost: le prix (nombre)
- currency: devise (EUR, USD, etc.)
- delivery_time: délai de livraison (format: "48h", "5d", etc.)

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte additionnel.
Si aucun tarif n'est trouvé, réponds avec un tableau vide [].

Exemple de format attendu:
[
  {
    "transport_mode": "road",
    "origin": { "city": "Paris", "country": "FR", "postal_code": "75000" },
    "destination": { "city": "Brussels", "country": "BE", "postal_code": "1000" },
    "weight_range": { "min": 0, "max": 1000 },
    "cost": 120.50,
    "currency": "EUR",
    "delivery_time": "48h"
  }
]`,
            },
          ],
        },
      ],
    });

    // Parser la réponse JSON
    const content = response.content[0];
    if (content.type === 'text') {
      try {
        // Nettoyer la réponse (enlever markdown si présent)
        let jsonText = content.text.trim();
        if (jsonText.startsWith('```')) {
          jsonText = jsonText.replace(/```json?\n?/g, '').replace(/```$/g, '');
        }
        return JSON.parse(jsonText);
      } catch (e) {
        console.error('Erreur parsing JSON:', e);
        return [];
      }
    }

    return [];
  }

  private async pdfToImages(buffer: Buffer): Promise<Buffer[]> {
    const converter = fromBuffer(buffer, {
      density: 200,
      format: 'png',
      width: 1654,
      height: 2339,
    });

    const images: Buffer[] = [];
    let page = 1;

    while (page <= 10) { // Limite à 10 pages
      try {
        const result = await converter(page);
        if (result.buffer) {
          images.push(result.buffer);
        }
        page++;
      } catch {
        break;
      }
    }

    return images;
  }
}
```

### 5.6 Parser PDF unifié

```typescript
// src/modules/partners/import/parsers/pdf.parser.ts

import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { FileParser, ParseResult, ParseOptions, ParsedRow } from './parser.interface';
import { PdfTextParser } from './pdf-text.parser';
import { PdfTabulaParser } from './pdf-tabula.parser';
import { PdfOcrParser } from './pdf-ocr.parser';
import { PdfAiParser } from './pdf-ai.parser';

@Injectable()
export class PdfParser implements FileParser {
  private readonly logger = new Logger(PdfParser.name);

  readonly supportedMimeTypes = ['application/pdf'];
  readonly supportedExtensions = ['.pdf'];

  constructor(
    private configService: ConfigService,
    private textParser: PdfTextParser,
    private tabulaParser: PdfTabulaParser,
    private ocrParser: PdfOcrParser,
    private aiParser: PdfAiParser,
  ) {}

  canParse(file: Express.Multer.File): boolean {
    return (
      this.supportedMimeTypes.includes(file.mimetype) ||
      file.originalname.toLowerCase().endsWith('.pdf')
    );
  }

  async parse(file: Express.Multer.File, options?: ParseOptions): Promise<ParseResult> {
    this.logger.log(`Parsing PDF: ${file.originalname}`);

    // Stratégie 1: Essayer l'extraction de texte simple
    let result = await this.tryTextExtraction(file.buffer);
    if (result.rows.length > 0) {
      this.logger.log('Extraction texte réussie');
      return result;
    }

    // Stratégie 2: Essayer Tabula pour les tableaux
    result = await this.tryTabulaExtraction(file.buffer);
    if (result.rows.length > 0) {
      this.logger.log('Extraction Tabula réussie');
      return result;
    }

    // Stratégie 3: OCR si activé
    if (options?.ocrEnabled) {
      result = await this.tryOcrExtraction(file.buffer);
      if (result.rows.length > 0) {
        this.logger.log('Extraction OCR réussie');
        return result;
      }
    }

    // Stratégie 4: IA comme dernier recours
    if (this.configService.get('ENABLE_AI_EXTRACTION')) {
      this.logger.log('Tentative extraction IA...');
      return this.tryAiExtraction(file.buffer);
    }

    return {
      success: false,
      rows: [],
      headers: [],
      errors: [{
        message: 'Impossible d\'extraire les données du PDF',
        type: 'extraction',
      }],
      metadata: {
        totalRows: 0,
        parsedRows: 0,
        fileType: 'pdf',
      },
    };
  }

  private async tryTextExtraction(buffer: Buffer): Promise<ParseResult> {
    try {
      const tables = await this.textParser.extractTables(buffer);
      return this.tablesToParseResult(tables, 'text');
    } catch (e) {
      this.logger.warn('Extraction texte échouée:', e.message);
      return this.emptyResult('text');
    }
  }

  private async tryTabulaExtraction(buffer: Buffer): Promise<ParseResult> {
    try {
      const tables = await this.tabulaParser.extractTables(buffer);
      if (tables.length === 0) return this.emptyResult('tabula');

      // Fusionner tous les tableaux
      const allRows: ParsedRow[] = [];
      let headers: string[] = [];

      for (const table of tables) {
        if (table.length > 0 && headers.length === 0) {
          headers = Object.keys(table[0]).map(h => this.normalizeHeader(h));
        }

        table.forEach((row, index) => {
          allRows.push({
            rowNumber: allRows.length + 1,
            data: this.normalizeRowKeys(row),
            raw: row,
          });
        });
      }

      return {
        success: true,
        rows: allRows,
        headers,
        errors: [],
        metadata: {
          totalRows: allRows.length,
          parsedRows: allRows.length,
          fileType: 'pdf-tabula',
        },
      };
    } catch (e) {
      this.logger.warn('Extraction Tabula échouée:', e.message);
      return this.emptyResult('tabula');
    }
  }

  private async tryOcrExtraction(buffer: Buffer): Promise<ParseResult> {
    try {
      const texts = await this.ocrParser.extractTextFromScannedPdf(buffer);
      // Traiter le texte OCR pour extraire les tableaux
      // ... logique similaire à tryTextExtraction
      return this.emptyResult('ocr');
    } catch (e) {
      this.logger.warn('Extraction OCR échouée:', e.message);
      return this.emptyResult('ocr');
    }
  }

  private async tryAiExtraction(buffer: Buffer): Promise<ParseResult> {
    try {
      const quotes = await this.aiParser.extractQuotesFromPdf(buffer);

      if (quotes.length === 0) {
        return this.emptyResult('ai');
      }

      const headers = [
        'transport_mode', 'origin_city', 'origin_country', 'origin_postal_code',
        'destination_city', 'destination_country', 'destination_postal_code',
        'weight_min', 'weight_max', 'volume_min', 'volume_max',
        'cost', 'currency', 'delivery_time',
      ];

      const rows: ParsedRow[] = quotes.map((quote, index) => ({
        rowNumber: index + 1,
        data: {
          transport_mode: quote.transport_mode,
          origin_city: quote.origin.city,
          origin_country: quote.origin.country,
          origin_postal_code: quote.origin.postal_code,
          destination_city: quote.destination.city,
          destination_country: quote.destination.country,
          destination_postal_code: quote.destination.postal_code,
          weight_min: quote.weight_range?.min,
          weight_max: quote.weight_range?.max,
          volume_min: quote.volume_range?.min,
          volume_max: quote.volume_range?.max,
          cost: quote.cost,
          currency: quote.currency,
          delivery_time: quote.delivery_time,
        },
        raw: quote,
      }));

      return {
        success: true,
        rows,
        headers,
        errors: [],
        metadata: {
          totalRows: rows.length,
          parsedRows: rows.length,
          fileType: 'pdf-ai',
        },
      };
    } catch (e) {
      this.logger.error('Extraction IA échouée:', e.message);
      return {
        success: false,
        rows: [],
        headers: [],
        errors: [{ message: e.message, type: 'extraction' }],
        metadata: { totalRows: 0, parsedRows: 0, fileType: 'pdf-ai' },
      };
    }
  }

  private tablesToParseResult(tables: string[][], method: string): ParseResult {
    if (tables.length < 2) return this.emptyResult(method);

    const headers = tables[0].map(h => this.normalizeHeader(h));
    const rows: ParsedRow[] = tables.slice(1).map((row, index) => {
      const data: Record<string, any> = {};
      headers.forEach((header, i) => {
        data[header] = row[i] || null;
      });
      return { rowNumber: index + 2, data, raw: row };
    });

    return {
      success: true,
      rows,
      headers,
      errors: [],
      metadata: {
        totalRows: rows.length,
        parsedRows: rows.length,
        fileType: `pdf-${method}`,
      },
    };
  }

  private emptyResult(method: string): ParseResult {
    return {
      success: false,
      rows: [],
      headers: [],
      errors: [],
      metadata: { totalRows: 0, parsedRows: 0, fileType: `pdf-${method}` },
    };
  }

  private normalizeHeader(header: string): string {
    return header
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '');
  }

  private normalizeRowKeys(row: Record<string, any>): Record<string, any> {
    const normalized: Record<string, any> = {};
    for (const [key, value] of Object.entries(row)) {
      normalized[this.normalizeHeader(key)] = value;
    }
    return normalized;
  }
}
```

---

## 6. Validation et transformation

### 6.1 Mapping des colonnes

```typescript
// src/modules/partners/import/transformers/column-mapper.ts

import { Injectable } from '@nestjs/common';

export interface ColumnMapping {
  sourceColumn: string;
  targetField: string;
  transform?: (value: any) => any;
  required?: boolean;
}

@Injectable()
export class ColumnMapper {
  // Mapping par défaut avec variantes de noms de colonnes
  private readonly defaultMappings: Record<string, string[]> = {
    transport_mode: ['mode_transport', 'mode', 'type_transport', 'transport_type', 'type'],
    origin_postal_code: ['origine_cp', 'origin_cp', 'cp_origine', 'code_postal_origine'],
    origin_city: ['origine_ville', 'origin_city', 'ville_origine', 'depart_ville', 'from_city'],
    origin_country: ['origine_pays', 'origin_country', 'pays_origine', 'depart_pays', 'from_country'],
    destination_postal_code: ['destination_cp', 'dest_cp', 'cp_destination', 'code_postal_dest'],
    destination_city: ['destination_ville', 'dest_city', 'ville_destination', 'arrivee_ville', 'to_city'],
    destination_country: ['destination_pays', 'dest_country', 'pays_destination', 'arrivee_pays', 'to_country'],
    weight_min: ['poids_min', 'weight_min', 'min_weight', 'poids_minimum'],
    weight_max: ['poids_max', 'weight_max', 'max_weight', 'poids_maximum'],
    volume_min: ['volume_min', 'min_volume', 'volume_minimum'],
    volume_max: ['volume_max', 'max_volume', 'volume_maximum'],
    cost: ['prix', 'price', 'tarif', 'cout', 'cost', 'montant', 'amount'],
    currency: ['devise', 'currency', 'monnaie'],
    delivery_time: ['delai', 'delivery_time', 'temps_livraison', 'delai_livraison', 'transit_time'],
    valid_until: ['validite', 'valid_until', 'date_validite', 'expiration', 'date_fin'],
  };

  detectMapping(headers: string[]): Map<string, string> {
    const mapping = new Map<string, string>();
    const normalizedHeaders = headers.map(h => this.normalize(h));

    for (const [targetField, sourceVariants] of Object.entries(this.defaultMappings)) {
      for (const variant of sourceVariants) {
        const index = normalizedHeaders.findIndex(h => h === variant || h.includes(variant));
        if (index !== -1) {
          mapping.set(headers[index], targetField);
          break;
        }
      }
    }

    return mapping;
  }

  applyMapping(row: Record<string, any>, mapping: Map<string, string>): Record<string, any> {
    const result: Record<string, any> = {};

    for (const [sourceCol, targetField] of mapping.entries()) {
      const normalizedSource = this.normalize(sourceCol);

      // Chercher la valeur dans le row avec différentes variantes de clé
      let value = row[sourceCol] ?? row[normalizedSource];

      // Si toujours pas trouvé, chercher par correspondance partielle
      if (value === undefined) {
        const rowKey = Object.keys(row).find(k =>
          this.normalize(k) === normalizedSource
        );
        if (rowKey) value = row[rowKey];
      }

      result[targetField] = value;
    }

    return result;
  }

  private normalize(str: string): string {
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }
}
```

### 6.2 Normalisation des données

```typescript
// src/modules/partners/import/transformers/data-normalizer.ts

import { Injectable } from '@nestjs/common';

@Injectable()
export class DataNormalizer {
  normalizeRow(row: Record<string, any>): Record<string, any> {
    return {
      transport_mode: this.normalizeTransportMode(row.transport_mode),
      origin_postal_code: this.normalizePostalCode(row.origin_postal_code),
      origin_city: this.normalizeCity(row.origin_city),
      origin_country: this.normalizeCountry(row.origin_country),
      destination_postal_code: this.normalizePostalCode(row.destination_postal_code),
      destination_city: this.normalizeCity(row.destination_city),
      destination_country: this.normalizeCountry(row.destination_country),
      weight_min: this.normalizeNumber(row.weight_min),
      weight_max: this.normalizeNumber(row.weight_max),
      volume_min: this.normalizeNumber(row.volume_min),
      volume_max: this.normalizeNumber(row.volume_max),
      cost: this.normalizeCost(row.cost),
      currency: this.normalizeCurrency(row.currency),
      delivery_time: this.normalizeDeliveryTime(row.delivery_time),
      valid_until: this.normalizeDate(row.valid_until),
    };
  }

  private normalizeTransportMode(value: any): string | null {
    if (!value) return null;

    const normalized = String(value).toLowerCase().trim();
    const mapping: Record<string, string> = {
      'route': 'road', 'routier': 'road', 'road': 'road', 'camion': 'road', 'truck': 'road',
      'rail': 'rail', 'train': 'rail', 'ferroviaire': 'rail', 'railway': 'rail',
      'mer': 'sea', 'maritime': 'sea', 'sea': 'sea', 'bateau': 'sea', 'ship': 'sea', 'ocean': 'sea',
      'air': 'air', 'aerien': 'air', 'avion': 'air', 'flight': 'air', 'plane': 'air',
      'multimodal': 'multimodal', 'combined': 'multimodal', 'multi': 'multimodal',
    };

    return mapping[normalized] || null;
  }

  private normalizePostalCode(value: any): string | null {
    if (!value) return null;
    return String(value).replace(/\s/g, '').toUpperCase();
  }

  private normalizeCity(value: any): string | null {
    if (!value) return null;
    return String(value)
      .trim()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  private normalizeCountry(value: any): string | null {
    if (!value) return null;

    const normalized = String(value).toUpperCase().trim();

    // Si déjà un code ISO
    if (/^[A-Z]{2}$/.test(normalized)) {
      return normalized;
    }

    // Mapping des noms de pays
    const countryMapping: Record<string, string> = {
      'FRANCE': 'FR', 'FRENCH': 'FR',
      'GERMANY': 'DE', 'ALLEMAGNE': 'DE', 'DEUTSCHLAND': 'DE',
      'BELGIUM': 'BE', 'BELGIQUE': 'BE', 'BELGIE': 'BE',
      'ITALY': 'IT', 'ITALIE': 'IT', 'ITALIA': 'IT',
      'SPAIN': 'ES', 'ESPAGNE': 'ES', 'ESPAÑA': 'ES',
      'UNITED KINGDOM': 'GB', 'UK': 'GB', 'ROYAUME-UNI': 'GB',
      'NETHERLANDS': 'NL', 'PAYS-BAS': 'NL', 'HOLLAND': 'NL',
      'PORTUGAL': 'PT',
      'SWITZERLAND': 'CH', 'SUISSE': 'CH', 'SCHWEIZ': 'CH',
      'AUSTRIA': 'AT', 'AUTRICHE': 'AT', 'ÖSTERREICH': 'AT',
      'POLAND': 'PL', 'POLOGNE': 'PL', 'POLSKA': 'PL',
      'CHINA': 'CN', 'CHINE': 'CN',
      'UNITED STATES': 'US', 'USA': 'US', 'ÉTATS-UNIS': 'US',
    };

    return countryMapping[normalized] || null;
  }

  private normalizeNumber(value: any): number | null {
    if (value === null || value === undefined || value === '') return null;

    if (typeof value === 'number') return value;

    // Nettoyer la chaîne
    const cleaned = String(value)
      .replace(/\s/g, '')
      .replace(',', '.')
      .replace(/[^0-9.-]/g, '');

    const num = parseFloat(cleaned);
    return isNaN(num) ? null : num;
  }

  private normalizeCost(value: any): number | null {
    const num = this.normalizeNumber(value);
    return num !== null && num > 0 ? Math.round(num * 100) / 100 : null;
  }

  private normalizeCurrency(value: any): string {
    if (!value) return 'EUR';

    const normalized = String(value).toUpperCase().trim();
    const validCurrencies = ['EUR', 'USD', 'GBP', 'CHF', 'CNY', 'JPY'];

    const mapping: Record<string, string> = {
      '€': 'EUR', 'EURO': 'EUR', 'EUROS': 'EUR',
      '$': 'USD', 'DOLLAR': 'USD', 'DOLLARS': 'USD',
      '£': 'GBP', 'POUND': 'GBP', 'LIVRE': 'GBP',
    };

    return validCurrencies.includes(normalized)
      ? normalized
      : (mapping[normalized] || 'EUR');
  }

  private normalizeDeliveryTime(value: any): string | null {
    if (!value) return null;

    const str = String(value).toLowerCase().trim();

    // Déjà au bon format
    if (/^\d+[hd]$/.test(str)) return str;

    // Extraire le nombre et l'unité
    const match = str.match(/(\d+)\s*(h|heure|heures|hour|hours|j|jour|jours|day|days|d)/i);
    if (match) {
      const num = parseInt(match[1]);
      const unit = match[2].toLowerCase();

      if (['h', 'heure', 'heures', 'hour', 'hours'].includes(unit)) {
        return `${num}h`;
      }
      if (['j', 'jour', 'jours', 'day', 'days', 'd'].includes(unit)) {
        return `${num}d`;
      }
    }

    // Nombre seul = jours par défaut
    const numOnly = parseInt(str);
    if (!isNaN(numOnly)) {
      return numOnly <= 72 ? `${numOnly}h` : `${numOnly}d`;
    }

    return null;
  }

  private normalizeDate(value: any): Date | null {
    if (!value) return null;

    if (value instanceof Date) return value;

    // Essayer différents formats
    const formats = [
      /^(\d{4})-(\d{2})-(\d{2})/, // YYYY-MM-DD
      /^(\d{2})\/(\d{2})\/(\d{4})/, // DD/MM/YYYY
      /^(\d{2})-(\d{2})-(\d{4})/, // DD-MM-YYYY
    ];

    const str = String(value).trim();

    for (const format of formats) {
      const match = str.match(format);
      if (match) {
        const date = new Date(str);
        if (!isNaN(date.getTime())) return date;
      }
    }

    return null;
  }
}
```

### 6.3 Validation métier

```typescript
// src/modules/partners/import/validators/row-validator.ts

import { Injectable } from '@nestjs/common';
import { validate } from 'class-validator';
import { plainToInstance } from 'class-transformer';
import { CreateQuoteDto } from '../../dto/create-quote.dto';

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  data?: CreateQuoteDto;
}

export interface ValidationError {
  field: string;
  value: any;
  message: string;
}

@Injectable()
export class RowValidator {
  async validateRow(
    rowNumber: number,
    data: Record<string, any>
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = [];

    // Validation des champs obligatoires
    if (!data.transport_mode) {
      errors.push({
        field: 'transport_mode',
        value: data.transport_mode,
        message: 'Mode de transport obligatoire',
      });
    }

    if (!data.origin_city || !data.origin_country) {
      errors.push({
        field: 'origin',
        value: `${data.origin_city}, ${data.origin_country}`,
        message: 'Origine (ville et pays) obligatoire',
      });
    }

    if (!data.destination_city || !data.destination_country) {
      errors.push({
        field: 'destination',
        value: `${data.destination_city}, ${data.destination_country}`,
        message: 'Destination (ville et pays) obligatoire',
      });
    }

    if (!data.cost || data.cost <= 0) {
      errors.push({
        field: 'cost',
        value: data.cost,
        message: 'Prix obligatoire et doit être positif',
      });
    }

    // Validation de cohérence
    if (data.origin_city === data.destination_city &&
        data.origin_country === data.destination_country) {
      errors.push({
        field: 'destination',
        value: null,
        message: 'L\'origine et la destination doivent être différentes',
      });
    }

    if (data.weight_min !== null && data.weight_max !== null &&
        data.weight_min > data.weight_max) {
      errors.push({
        field: 'weight_range',
        value: `${data.weight_min}-${data.weight_max}`,
        message: 'Le poids minimum ne peut pas être supérieur au maximum',
      });
    }

    if (data.volume_min !== null && data.volume_max !== null &&
        data.volume_min > data.volume_max) {
      errors.push({
        field: 'volume_range',
        value: `${data.volume_min}-${data.volume_max}`,
        message: 'Le volume minimum ne peut pas être supérieur au maximum',
      });
    }

    if (data.valid_until && new Date(data.valid_until) < new Date()) {
      errors.push({
        field: 'valid_until',
        value: data.valid_until,
        message: 'La date de validité doit être dans le futur',
      });
    }

    // Transformation en DTO pour validation class-validator
    if (errors.length === 0) {
      const dto = plainToInstance(CreateQuoteDto, this.toDto(data));
      const classErrors = await validate(dto);

      if (classErrors.length > 0) {
        for (const error of classErrors) {
          errors.push({
            field: error.property,
            value: error.value,
            message: Object.values(error.constraints || {}).join(', '),
          });
        }
      }

      return {
        isValid: errors.length === 0,
        errors,
        data: errors.length === 0 ? dto : undefined,
      };
    }

    return { isValid: false, errors };
  }

  private toDto(data: Record<string, any>): Partial<CreateQuoteDto> {
    return {
      transport_mode: data.transport_mode,
      origin: {
        postal_code: data.origin_postal_code,
        city: data.origin_city,
        country: data.origin_country,
      },
      destination: {
        postal_code: data.destination_postal_code,
        city: data.destination_city,
        country: data.destination_country,
      },
      weight_range: data.weight_min || data.weight_max ? {
        min: data.weight_min ?? 0,
        max: data.weight_max ?? 999999,
      } : undefined,
      volume_range: data.volume_min || data.volume_max ? {
        min: data.volume_min ?? 0,
        max: data.volume_max ?? 999999,
      } : undefined,
      cost: data.cost,
      currency: data.currency || 'EUR',
      delivery_time: data.delivery_time,
      valid_until: data.valid_until?.toISOString(),
    };
  }
}
```

---

## 7. Gestion des erreurs

### 7.1 Service d'import complet

```typescript
// src/modules/partners/import/import.service.ts

import { Injectable, Logger } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bull';
import { Queue } from 'bull';
import { PrismaService } from '../../../shared/database/prisma.service';
import { ParserFactory } from './parsers/parser.factory';
import { ColumnMapper } from './transformers/column-mapper';
import { DataNormalizer } from './transformers/data-normalizer';
import { RowValidator } from './validators/row-validator';

export interface ImportResult {
  jobId: string;
  status: 'completed' | 'partial' | 'failed';
  summary: {
    totalRows: number;
    successCount: number;
    errorCount: number;
    skippedCount: number;
  };
  errors: ImportRowError[];
  createdQuoteIds: string[];
}

export interface ImportRowError {
  rowNumber: number;
  errors: Array<{ field: string; message: string; value: any }>;
  rawData: Record<string, any>;
}

@Injectable()
export class ImportService {
  private readonly logger = new Logger(ImportService.name);

  constructor(
    private prisma: PrismaService,
    private parserFactory: ParserFactory,
    private columnMapper: ColumnMapper,
    private dataNormalizer: DataNormalizer,
    private rowValidator: RowValidator,
    @InjectQueue('import') private importQueue: Queue,
  ) {}

  async importFile(
    partnerId: string,
    file: Express.Multer.File,
    options?: { mode: 'append' | 'replace' }
  ): Promise<ImportResult> {
    const jobId = `import_${partnerId}_${Date.now()}`;

    this.logger.log(`Démarrage import ${jobId}: ${file.originalname}`);

    // 1. Parser le fichier
    const parser = this.parserFactory.getParser(file);
    const parseResult = await parser.parse(file);

    if (!parseResult.success || parseResult.rows.length === 0) {
      return {
        jobId,
        status: 'failed',
        summary: {
          totalRows: 0,
          successCount: 0,
          errorCount: 1,
          skippedCount: 0,
        },
        errors: [{
          rowNumber: 0,
          errors: parseResult.errors.map(e => ({
            field: e.column || 'file',
            message: e.message,
            value: null,
          })),
          rawData: {},
        }],
        createdQuoteIds: [],
      };
    }

    // 2. Détecter le mapping des colonnes
    const columnMapping = this.columnMapper.detectMapping(parseResult.headers);

    this.logger.log(`Mapping détecté: ${JSON.stringify([...columnMapping.entries()])}`);

    // 3. Si mode replace, désactiver les anciens tarifs
    if (options?.mode === 'replace') {
      await this.prisma.partnerQuote.updateMany({
        where: { partnerId, isActive: true },
        data: { isActive: false },
      });
    }

    // 4. Traiter chaque ligne
    const errors: ImportRowError[] = [];
    const createdQuoteIds: string[] = [];
    let successCount = 0;
    let skippedCount = 0;

    for (const row of parseResult.rows) {
      try {
        // Appliquer le mapping
        const mappedData = this.columnMapper.applyMapping(row.data, columnMapping);

        // Normaliser les données
        const normalizedData = this.dataNormalizer.normalizeRow(mappedData);

        // Valider
        const validation = await this.rowValidator.validateRow(row.rowNumber, normalizedData);

        if (!validation.isValid) {
          errors.push({
            rowNumber: row.rowNumber,
            errors: validation.errors,
            rawData: row.data,
          });
          continue;
        }

        // Insérer en base
        const quote = await this.createQuote(partnerId, validation.data!);
        createdQuoteIds.push(quote.id);
        successCount++;

      } catch (error) {
        this.logger.error(`Erreur ligne ${row.rowNumber}:`, error);
        errors.push({
          rowNumber: row.rowNumber,
          errors: [{ field: 'system', message: error.message, value: null }],
          rawData: row.data,
        });
      }
    }

    const status = errors.length === 0
      ? 'completed'
      : successCount > 0 ? 'partial' : 'failed';

    this.logger.log(
      `Import ${jobId} terminé: ${successCount} succès, ${errors.length} erreurs`
    );

    return {
      jobId,
      status,
      summary: {
        totalRows: parseResult.rows.length,
        successCount,
        errorCount: errors.length,
        skippedCount,
      },
      errors,
      createdQuoteIds,
    };
  }

  async importFileAsync(
    partnerId: string,
    file: Express.Multer.File,
    options?: { mode: 'append' | 'replace' }
  ): Promise<{ jobId: string }> {
    // Sauvegarder le fichier temporairement
    const job = await this.importQueue.add('process-import', {
      partnerId,
      fileName: file.originalname,
      fileBuffer: file.buffer.toString('base64'),
      mimeType: file.mimetype,
      options,
    });

    return { jobId: job.id.toString() };
  }

  private async createQuote(partnerId: string, data: any) {
    return this.prisma.partnerQuote.create({
      data: {
        partnerId,
        transportMode: data.transport_mode.toUpperCase(),
        originPostalCode: data.origin?.postal_code,
        originCity: data.origin?.city,
        originCountry: data.origin?.country,
        destPostalCode: data.destination?.postal_code,
        destCity: data.destination?.city,
        destCountry: data.destination?.country,
        weightMin: data.weight_range?.min,
        weightMax: data.weight_range?.max,
        volumeMin: data.volume_range?.min,
        volumeMax: data.volume_range?.max,
        cost: data.cost,
        currency: data.currency,
        deliveryTime: data.delivery_time,
        validUntil: data.valid_until ? new Date(data.valid_until) : null,
        isActive: true,
      },
    });
  }
}
```

### 7.2 Rapport d'erreurs

```typescript
// src/modules/partners/import/import.controller.ts

import {
  Controller,
  Post,
  Get,
  Param,
  UseInterceptors,
  UploadedFile,
  Body,
  UseGuards,
  Res,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiKeyGuard } from '../../auth/guards/api-key.guard';
import { CurrentPartner } from '../../auth/decorators/current-partner.decorator';
import { ImportService } from './import.service';
import { Response } from 'express';
import * as ExcelJS from 'exceljs';

@Controller('v1/partners/quotes')
@UseGuards(ApiKeyGuard)
export class ImportController {
  constructor(private importService: ImportService) {}

  @Post('import')
  @UseInterceptors(FileInterceptor('file', {
    limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB max
    fileFilter: (req, file, cb) => {
      const allowed = ['.csv', '.xlsx', '.xls', '.pdf'];
      const ext = file.originalname.slice(file.originalname.lastIndexOf('.'));
      cb(null, allowed.includes(ext.toLowerCase()));
    },
  }))
  async importFile(
    @CurrentPartner() partner: { id: string },
    @UploadedFile() file: Express.Multer.File,
    @Body('mode') mode: 'append' | 'replace' = 'append',
  ) {
    const result = await this.importService.importFile(partner.id, file, { mode });

    return {
      success: result.status !== 'failed',
      ...result,
    };
  }

  @Post('import/async')
  @UseInterceptors(FileInterceptor('file'))
  async importFileAsync(
    @CurrentPartner() partner: { id: string },
    @UploadedFile() file: Express.Multer.File,
    @Body('mode') mode: 'append' | 'replace' = 'append',
  ) {
    const { jobId } = await this.importService.importFileAsync(
      partner.id, file, { mode }
    );

    return {
      jobId,
      status: 'processing',
      message: 'Import en cours de traitement',
      checkStatusUrl: `/v1/partners/quotes/import/status/${jobId}`,
    };
  }

  @Get('import/status/:jobId')
  async getImportStatus(@Param('jobId') jobId: string) {
    // Récupérer le statut depuis la queue ou la base
    // ...
  }

  @Get('import/:jobId/errors/download')
  async downloadErrorReport(
    @Param('jobId') jobId: string,
    @Res() res: Response,
  ) {
    // Récupérer les erreurs depuis le cache/DB
    const importResult = await this.getImportResult(jobId);

    if (!importResult || importResult.errors.length === 0) {
      return res.status(404).json({ message: 'Aucune erreur à télécharger' });
    }

    // Générer le fichier Excel des erreurs
    const workbook = new ExcelJS.Workbook();
    const sheet = workbook.addWorksheet('Erreurs Import');

    // Headers
    sheet.columns = [
      { header: 'Ligne', key: 'row', width: 10 },
      { header: 'Champ', key: 'field', width: 20 },
      { header: 'Valeur', key: 'value', width: 30 },
      { header: 'Erreur', key: 'message', width: 50 },
      { header: 'Données brutes', key: 'raw', width: 100 },
    ];

    // Style header
    sheet.getRow(1).font = { bold: true };
    sheet.getRow(1).fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' },
    };

    // Données
    for (const error of importResult.errors) {
      for (const err of error.errors) {
        sheet.addRow({
          row: error.rowNumber,
          field: err.field,
          value: err.value,
          message: err.message,
          raw: JSON.stringify(error.rawData),
        });
      }
    }

    // Envoyer le fichier
    res.setHeader(
      'Content-Type',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    );
    res.setHeader(
      'Content-Disposition',
      `attachment; filename=erreurs_import_${jobId}.xlsx`
    );

    await workbook.xlsx.write(res);
    res.end();
  }

  private async getImportResult(jobId: string) {
    // Implémenter la récupération depuis cache/DB
    return null;
  }
}
```

---

## 8. Interface utilisateur

### 8.1 Workflow d'import avec prévisualisation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW D'IMPORT                                    │
│                                                                              │
│  Étape 1: Upload                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐                                                │   │
│  │  │  📁 Drag & Drop │  Formats supportés: CSV, Excel, PDF           │   │
│  │  │    ou cliquer   │  Taille max: 10 MB                            │   │
│  │  └─────────────────┘                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  Étape 2: Mapping des colonnes                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Colonne fichier        →      Champ système                        │   │
│  │  ─────────────────────────────────────────────                      │   │
│  │  "Mode Transport"       →      transport_mode     ✓ Auto-détecté   │   │
│  │  "Prix unitaire"        →      cost               ✓ Auto-détecté   │   │
│  │  "Ville départ"         →      [Sélectionner...] ▼                 │   │
│  │  "Code postal arrivée"  →      destination_postal_code ✓           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  Étape 3: Prévisualisation                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Aperçu des 5 premières lignes:                                     │   │
│  │  ┌─────┬──────────┬────────────┬──────────┬───────┐                │   │
│  │  │ #   │ Mode     │ Origine    │ Dest.    │ Prix  │                │   │
│  │  ├─────┼──────────┼────────────┼──────────┼───────┤                │   │
│  │  │ 1   │ road     │ Paris, FR  │ Brussels │ 120€  │ ✅             │   │
│  │  │ 2   │ rail     │ Lyon, FR   │ Milan    │ 250€  │ ✅             │   │
│  │  │ 3   │ ???      │ Marseille  │ ???      │ -50€  │ ⚠️ 2 erreurs  │   │
│  │  └─────┴──────────┴────────────┴──────────┴───────┘                │   │
│  │                                                                     │   │
│  │  ⚠️ 3 lignes avec erreurs sur 150                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  Étape 4: Confirmation                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ○ Ajouter aux tarifs existants                                     │   │
│  │  ○ Remplacer tous les tarifs                                        │   │
│  │                                                                     │   │
│  │  □ Ignorer les lignes en erreur et continuer                       │   │
│  │                                                                     │   │
│  │  [Annuler]                              [Importer 147 tarifs]       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 API de prévisualisation

```typescript
// Endpoint de prévisualisation
@Post('import/preview')
@UseInterceptors(FileInterceptor('file'))
async previewImport(
  @UploadedFile() file: Express.Multer.File,
): Promise<ImportPreview> {
  const parser = this.parserFactory.getParser(file);
  const parseResult = await parser.parse(file);

  const columnMapping = this.columnMapper.detectMapping(parseResult.headers);

  // Valider les 10 premières lignes
  const previewRows = [];
  for (const row of parseResult.rows.slice(0, 10)) {
    const mappedData = this.columnMapper.applyMapping(row.data, columnMapping);
    const normalizedData = this.dataNormalizer.normalizeRow(mappedData);
    const validation = await this.rowValidator.validateRow(row.rowNumber, normalizedData);

    previewRows.push({
      rowNumber: row.rowNumber,
      original: row.data,
      normalized: normalizedData,
      isValid: validation.isValid,
      errors: validation.errors,
    });
  }

  return {
    totalRows: parseResult.rows.length,
    detectedMapping: Object.fromEntries(columnMapping),
    unmappedColumns: parseResult.headers.filter(h => !columnMapping.has(h)),
    preview: previewRows,
    validCount: previewRows.filter(r => r.isValid).length,
    errorCount: previewRows.filter(r => !r.isValid).length,
  };
}
```

---

## 9. Comparatif des solutions PDF

| Solution | Coût | Précision | Complexité | Cas d'usage |
|----------|------|-----------|------------|-------------|
| **pdf-parse** | Gratuit | 60-70% | Faible | PDF texte simple |
| **Tabula** | Gratuit | 80-90% | Moyenne | Tableaux structurés |
| **Tesseract OCR** | Gratuit | 70-85% | Élevée | PDF scannés |
| **Claude/GPT-4** | ~0.02€/page | 90-98% | Moyenne | Formats variables |
| **Amazon Textract** | ~0.015€/page | 90-95% | Moyenne | Production AWS |
| **Google Document AI** | ~0.01€/page | 90-95% | Moyenne | Production GCP |

### Recommandation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRATÉGIE RECOMMANDÉE (HYBRIDE)                          │
│                                                                              │
│  1. Essayer pdf-parse (gratuit, rapide)                                     │
│     │                                                                        │
│     ├─► Succès → Utiliser les données                                       │
│     │                                                                        │
│     └─► Échec → Étape 2                                                     │
│                                                                              │
│  2. Essayer Tabula (gratuit, tableaux)                                      │
│     │                                                                        │
│     ├─► Succès → Utiliser les données                                       │
│     │                                                                        │
│     └─► Échec → Étape 3                                                     │
│                                                                              │
│  3. IA (Claude) - Dernier recours                                           │
│     │                                                                        │
│     └─► Extraction avec validation humaine                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Dépendances à installer

```bash
# Parsing CSV/Excel
npm install papaparse exceljs iconv-lite

# Parsing PDF (texte)
npm install pdf-parse

# Conversion PDF → Image
npm install pdf2pic sharp

# OCR
npm install tesseract.js

# IA (optionnel)
npm install @anthropic-ai/sdk
# ou
npm install openai

# Types
npm install -D @types/papaparse
```

---

## Résumé

| Format | Solution recommandée | Librairie |
|--------|---------------------|-----------|
| **CSV** | PapaParse | `papaparse` |
| **Excel** | ExcelJS | `exceljs` |
| **PDF texte** | pdf-parse + Tabula | `pdf-parse` + Python |
| **PDF scanné** | Tesseract ou IA | `tesseract.js` ou Claude |
| **PDF complexe** | Claude/GPT-4 Vision | `@anthropic-ai/sdk` |

Le système hybride proposé permet de minimiser les coûts (priorité aux solutions gratuites) tout en garantissant une extraction fiable grâce à l'IA en dernier recours.
