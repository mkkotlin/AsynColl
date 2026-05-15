import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

// Guard to check if user is authenticated before accessing protected routes
export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = localStorage.getItem('access');

  if (token) {
    return true;
  }

  router.navigate(['/login']);
  return false;
};
