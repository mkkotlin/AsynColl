import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  // Board operations
  getBoards() {
    return this.http.get(`${this.baseUrl}/boards/`);
  }

  getBoard(id: number) {
    return this.http.get(`${this.baseUrl}/boards/${id}/`);
  }

  // Card CRUD operations
  getUser() {
    return this.http.get(`${this.baseUrl}/users/`);
  }

  createCard(data: any) {
    return this.http.post(`${this.baseUrl}/cards/`, data);
  }

  updateCard(id: number, data: any) {
    return this.http.patch(`${this.baseUrl}/cards/${id}/`, data);
  }

  // List reordering for drag-drop
  reorderList(listId: number, cardIds: number[]) {
    return this.http.post(`${this.baseUrl}/lists/${listId}/reorder/`, { card_ids: cardIds });
  }

  // Authentication
  login(data: any) {
    return this.http.post(`${this.baseUrl}/token/`, data);
  }

  register(data: any) {
    return this.http.post(`${this.baseUrl}/register/`, data);
  }
}