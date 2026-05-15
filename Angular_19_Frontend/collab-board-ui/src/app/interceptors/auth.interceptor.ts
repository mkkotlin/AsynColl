import {
  HttpErrorResponse,
  HttpInterceptorFn
} from '@angular/common/http';

import { inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, switchMap, throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {

  const token = localStorage.getItem('access');

  const http = inject(HttpClient);

  // 🔹 Add access token
  if (token) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  return next(req).pipe(

    catchError((error: HttpErrorResponse) => {

      // 🔥 Access token expired
      if (error.status === 401) {

        const refresh = localStorage.getItem('refresh');

        // 🔹 Try refresh token
        return http.post<any>(
          'http://127.0.0.1:8000/api/token/refresh/',
          { refresh }
        ).pipe(

          switchMap((res) => {

            // Save new access token
            localStorage.setItem('access', res.access);

            // Retry original request
            const clonedReq = req.clone({
              setHeaders: {
                Authorization: `Bearer ${res.access}`
              }
            });

            return next(clonedReq);
          }),

          catchError((refreshError) => {

            // Refresh failed → logout
            localStorage.clear();

            return throwError(() => refreshError);
          })

        );
      }

      return throwError(() => error);

    })

  );
};