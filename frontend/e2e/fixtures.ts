/**
 * fixtures.ts — Fixtures partagées pour les tests E2E Playwright
 *
 * Usage dans un spec :
 *   import { loginAs, expectForbidden } from './fixtures';
 *   await loginAs(page, request, 'admin');
 */
import { Page, APIRequestContext } from '@playwright/test';

export type E2ERole = 'admin' | 'super_admin' | 'commercial' | 'operator' | 'viewer';

// Helper pour lire les variables d'environnement sans dépendre de @types/node
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const env = (key: string, fallback: string): string =>
    ((globalThis as Record<string, unknown>)['process'] as Record<string, Record<string, string>> | undefined)
        ?.env?.[key] ?? fallback;

/**
 * Credentials de test stables (correspondant à l'utilisateur créé par initial_data.py
 * ou un script de seed E2E).
 * Ces valeurs peuvent être surchargées via les variables d'environnement.
 */
const CREDENTIALS: Record<E2ERole, { login: string; password: string }> = {
    admin: { login: env('E2E_ADMIN_LOGIN', 'admin'), password: env('E2E_ADMIN_PASSWORD', 'Admin1234!') },
    super_admin: { login: env('E2E_SUPER_ADMIN_LOGIN', 'super_admin'), password: env('E2E_SUPER_ADMIN_PASSWORD', 'Admin1234!') },
    commercial: { login: env('E2E_COMMERCIAL_LOGIN', 'commercial'), password: env('E2E_COMMERCIAL_PASSWORD', 'Admin1234!') },
    operator: { login: env('E2E_OPERATOR_LOGIN', 'operator'), password: env('E2E_OPERATOR_PASSWORD', 'Admin1234!') },
    viewer: { login: env('E2E_VIEWER_LOGIN', 'viewer'), password: env('E2E_VIEWER_PASSWORD', 'Admin1234!') },
};

/**
 * Connecte un utilisateur de façon rapide via l'API (sans passer par l'UI de login).
 * Stocke l'access_token et le refresh_token dans localStorage.
 *
 * @param page       La page Playwright
 * @param request    L'objet APIRequestContext fourni par la fixture Playwright
 * @param role       Le rôle à utiliser pour se connecter
 */
export async function loginAs(page: Page, request: APIRequestContext, role: E2ERole): Promise<void> {
    const { login, password } = CREDENTIALS[role];
    const baseURL = env('E2E_BASE_URL', 'http://localhost');

    const response = await request.post(`${baseURL}/api/v1/auth/login`, {
        form: { username: login, password },
    });

    if (!response.ok()) {
        throw new Error(
            `loginAs("${role}") failed: HTTP ${response.status()} — ` +
            `login="${login}". Vérifier que l'utilisateur existe en DB.`
        );
    }

    const { access_token, refresh_token } = await response.json();

    // Charger une page quelconque pour initialiser l'origine avant d'écrire en localStorage
    await page.goto('/');
    await page.evaluate(
        ({ at, rt }) => {
            localStorage.setItem('access_token', at);
            localStorage.setItem('refresh_token', rt);
        },
        { at: access_token, rt: refresh_token }
    );
}

/**
 * Vérifie que la page affiche un message 403 / redirection vers login.
 * Adapter si le composant ProtectedRoute redirige vers une autre URL.
 */
export async function expectForbidden(page: Page): Promise<void> {
    const url = page.url();
    const isForbidden =
        url.includes('/login') ||
        url.includes('/403') ||
        (await page.getByText(/403|accès refusé|non autorisé/i).isVisible().catch(() => false));

    if (!isForbidden) {
        throw new Error(`expectForbidden: aucune redirection 403/login détectée — URL courante : ${url}`);
    }
}
