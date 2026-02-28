import { test, expect } from '@playwright/test';
import { loginAs } from './fixtures';

test.describe('Authentication Flow', () => {

    // 1.1 — Login valide → redirect vers dashboard
    test('should allow user to login with valid credentials', async ({ page }) => {
        await page.goto('/login');

        await page.fill('input[name="email"]', 'admin');
        await page.fill('input[name="password"]', 'Admin1234!');
        await page.click('button[type="submit"]');

        // Attendre la redirection post-login
        await page.waitForURL(/\/(dashboard|$)/, { timeout: 8000 });
        await expect(page).not.toHaveURL(/\/login/);
    });

    // 1.2 — Mauvais mot de passe → message d'erreur visible
    test('should show error on invalid credentials', async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'wrong@example.com');
        await page.fill('input[name="password"]', 'WrongPass123!');
        await page.click('button[type="submit"]');

        // Vérifier le message d'erreur (toast ou alerte)
        await expect(
            page.getByText(/email ou mot de passe incorrect|identifiants incorrects|invalid/i)
        ).toBeVisible({ timeout: 5000 });
    });

    // 1.3 — Compte inactif → message d'erreur approprié
    test('should show error for inactive account', async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'inactive_user');
        await page.fill('input[name="password"]', 'Admin1234!');
        await page.click('button[type="submit"]');

        await expect(
            page.getByText(/compte inactif|compte désactivé|inactive/i)
        ).toBeVisible({ timeout: 5000 });
    });

    // 1.4 — Logout → redirect vers /login
    test('should redirect to login after logout', async ({ page, request }) => {
        await loginAs(page, request, 'admin');
        await page.goto('/dashboard');
        // Clic sur le bouton de déconnexion (adapter le sélecteur si nécessaire)
        await page.getByRole('button', { name: /déconnexion|logout|sign out/i }).click();
        await page.waitForURL(/\/login/, { timeout: 5000 });
        await expect(page).toHaveURL(/\/login/);
    });

    // 1.5 — Route protégée sans connexion → redirect vers /login
    test('should redirect unauthenticated user to login', async ({ page }) => {
        // Pas de loginAs → aucun token en localStorage
        await page.goto('/dashboard');
        await page.waitForURL(/\/login/, { timeout: 5000 });
        await expect(page).toHaveURL(/\/login/);
    });

    // 1.6 — must_change_password=true → modale de changement de MDP
    test('should open password change modal when required', async ({ page, request }) => {
        // Ce test suppose l'existence d'un user avec must_change_password=true
        // Adapter le login selon l'environnement de test
        await loginAs(page, request, 'viewer');
        await page.goto('/dashboard');
        await expect(
            page.getByRole('dialog').filter({ hasText: /changer.*mot de passe|change.*password/i })
        ).toBeVisible({ timeout: 5000 });
    });

    // 1.7 — Token expiré → redirect automatique vers /login
    test('should redirect to login when token is expired', async ({ page }) => {
        // Injecter un JWT expiré directement en localStorage
        await page.goto('/');
        await page.evaluate(() => {
            // JWT minimal avec exp = epoch (janvier 1970 — expiré depuis longtemps)
            const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
                btoa(JSON.stringify({ sub: 'test', exp: 1, jti: 'test' })).replace(/=/g, '') +
                '.invalid_signature';
            localStorage.setItem('access_token', expiredToken);
            localStorage.setItem('refresh_token', 'invalid_refresh');
        });

        await page.goto('/dashboard');
        await page.waitForURL(/\/login/, { timeout: 8000 });
        await expect(page).toHaveURL(/\/login/);
    });
});
