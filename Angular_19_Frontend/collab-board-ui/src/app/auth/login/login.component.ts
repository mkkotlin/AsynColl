import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.component.html'
})
export class LoginComponent {

  username = '';
  password = '';

  constructor(
    private api: ApiService,
    private router: Router
  ) {}

  login() {

    this.api.login({
      username: this.username,
      password: this.password
    }).subscribe((res: any) => {

      localStorage.setItem('access', res.access);
      localStorage.setItem('refresh', res.refresh);

      this.router.navigate(['/board']);

    });

  }
}